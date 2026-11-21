"""Enriquece el catálogo con imágenes y especificaciones desde las fichas oficiales."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import time
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/catalog_pages"
IMAGES = ROOT / "assistant/static/products"
ASSETS = ROOT / "assistant/catalog/product_assets.json"
UA = "Mozilla/5.0 (compatible; AsistenteCarvajal/1.0; +https://github.com/almeneses/asistente-carvajal)"
META_IMAGE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I)
META_DESC = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', re.I)


def _clean_text(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


def _first(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    return html.unescape(match.group(1)).strip() if match else ""


def parse_page(raw: str) -> dict[str, object]:
    text = _clean_text(raw)
    image = _first(META_IMAGE.pattern, raw)
    markers = [
        (r"Largo \(cm\):\s*([\d.,]+)", "length_cm"),
        (r"Ancho \(cm\):\s*([\d.,]+)", "width_cm"),
        (r"Alto \(cm\):\s*([\d.,]+)", "height_cm"),
        (r"Peso \(kg\):\s*([\d.,]+)", "weight_kg"),
        (r"Marca:\s*(.+?)\s+(?:Materiales|Material):", "brand_text"),
        (r"Materiales?:\s*(.+?)\s+Temperatura de uso", "materials_text"),
        (r"Temperatura de uso recomendada:\s*(.+?)\s+Color:", "temperature_text"),
        (r"Color:\s*(.+?)\s+Cantidad por caja:", "color"),
        (r"Cantidad por caja:\s*([\d.,]+)", "units_per_box_page"),
    ]
    specs = {key: _first(pattern, text) for pattern, key in markers}
    description = html.unescape(_first(META_DESC.pattern, raw))
    return {"image_url": image, "description": description, **specs}


def fetch_page(url: str) -> str | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if cached.is_file():
        return cached.read_text(encoding="utf-8", errors="ignore")
    for attempt in range(3):
        try:
            response = httpx.get(url, headers={"User-Agent": UA}, timeout=25, follow_redirects=True)
            if response.status_code == 200:
                cached.write_text(response.text, encoding="utf-8")
                return response.text
        except httpx.HTTPError:
            pass
        time.sleep(1 + attempt)
    return None


def download_image(url: str, sku: str) -> str | None:
    if not url:
        return None
    IMAGES.mkdir(parents=True, exist_ok=True)
    output = IMAGES / f"{sku}.webp"
    if output.is_file() and output.stat().st_size > 0:
        return f"/static/products/{sku}.webp"
    temporary = CACHE / f"{sku}.img"
    try:
        with httpx.stream(
            "GET",
            url,
            headers={"User-Agent": UA},
            timeout=30,
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(temporary),
                "-vf",
                "scale=600:600:force_original_aspect_ratio=decrease,"
                "pad=600:600:(ow-iw)/2:(oh-ih)/2:color=white",
                "-quality",
                "80",
                str(output),
            ],
            check=True,
        )
        return f"/static/products/{sku}.webp"
    except (httpx.HTTPError, subprocess.CalledProcessError, OSError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Limita referencias (pruebas).")
    args = parser.parse_args()
    catalog_dir = Path(
        os.environ.get("CATALOG_DIR", str(ROOT.parent / "carvajal/data/catalog/empaques"))
    )
    rows = list(csv.DictReader((catalog_dir / "referencias.csv").open(encoding="utf-8")))
    if args.limit:
        rows = rows[: args.limit]
    assets: dict[str, dict[str, object]] = {}
    if ASSETS.is_file():
        assets = json.loads(ASSETS.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    for index, row in enumerate(rows, 1):
        sku = row.get("sku", "").strip()
        url = row.get("source_url", "").strip()
        if not sku or not url:
            continue
        raw = fetch_page(url)
        if not raw:
            print(f"[{index}/{len(rows)}] {sku} sin ficha")
            continue
        parsed = parse_page(raw)
        image = download_image(str(parsed.pop("image_url", "")), sku)
        assets[sku] = {
            **parsed,
            "image": image,
            "source_url": url,
            "captured_at": row.get("captured_at") or today,
        }
        print(f"[{index}/{len(rows)}] {sku} imagen={'sí' if image else 'no'}")
        time.sleep(0.15)
    ASSETS.write_text(
        json.dumps(dict(sorted(assets.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    IMAGES.mkdir(parents=True, exist_ok=True)
    with_images = sum(1 for value in assets.values() if value.get("image"))
    (IMAGES / "README.md").write_text(
        "# Imágenes de producto\n\n"
        "Imágenes y especificaciones obtenidas de las fichas oficiales de Carvajal Empaques\n"
        "(`source_url` en `assistant/catalog/product_assets.json`, campo `captured_at`).\n"
        "Uso exclusivo para el asistente; no se redistribuyen como catálogo independiente.\n\n"
        f"Referencias con imagen: {with_images}/{len(assets)}.\n",
        encoding="utf-8",
    )
    print(f"Listo: {with_images}/{len(assets)} con imagen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
