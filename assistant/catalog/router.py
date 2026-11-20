"""Router determinista y extracción de atributos del catálogo."""

from __future__ import annotations

import re
import unicodedata

from assistant.catalog.models import ExtractedQuery

_FAMILIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("tapa", ("tapa", "tapas", "tapon", "tapones")),
    ("vaso", ("vaso", "vasos", "vasito", "vasitos")),
    (
        "contenedor",
        (
            "contenedor",
            "contenedores",
            "portacomida",
            "portacomidas",
            "cazuela",
            "cazuelas",
            "bowl",
            "bowls",
        ),
    ),
    ("plato", ("plato", "platos", "platillo", "platillos")),
    ("charola", ("charola", "charolas", "bandeja", "bandejas")),
    (
        "cubierto",
        (
            "cubierto",
            "cubiertos",
            "tenedor",
            "tenedores",
            "cuchara",
            "cucharas",
            "cuchillo",
            "cuchillos",
        ),
    ),
    ("envase", ("envase", "envases", "pote", "potes")),
    ("bolsa", ("bolsa", "bolsas")),
)
_DOC_KEYWORDS = (
    "carvajal",
    "historia",
    "fundada",
    "fundacion",
    "sectores",
    "sector",
    "proposito",
    "valores",
    "principios",
    "gobierno",
    "etica",
    "compromiso",
    "sostenibilidad",
    "noticias",
    "inversion",
    "inversionistas",
    "fundaciones",
    "paises",
    "presencia",
    "ingresos",
    "ebitda",
    "utilidad",
    "perdida",
    "activos",
    "pasivos",
    "patrimonio",
    "empleados",
    "contactar",
    "contacto",
    "bioform",
    "liquidezya",
    "mepal",
    "espacios",
    "educacion",
    "tecnologia",
    "comunicacion",
    "papel",
    "organizacion",
    "empresa",
    "linea etica",
    "propiedades e inversiones",
    "norma",
    "assenda",
)
_PRICE_WORDS = (
    "precio",
    "precios",
    "cuanto cuesta",
    "cuanto cuestan",
    "cuanto valen",
    "cuanto vale",
    "costo",
    "costos",
    "total",
    "cotiza",
    "cotizacion",
    "factura",
)
_QUANTITY_WORDS = ("necesito", "necesitamos", "busco", "buscamos", "quiero")
_DISTRIBUTOR_WORDS = (
    "distribuidor",
    "distribuidores",
    "distribuye",
    "distribuyen",
    "proveedor",
    "proveedores",
    "donde comprar",
    "punto de venta",
    "puntos de venta",
)
_COMMERCIAL_DESCRIPTORS = (
    "flexible",
    "flexibles",
    "agroindustrial",
    "termoformado",
    "termoformados",
    "a la medida",
    "medida",
    "exportar",
    "flores",
    "corrugada",
    "corrugadas",
    "corrugado",
    "industrial",
)
_RENEWABLE_WORDS = (
    "papel",
    "pulpa",
    "fibra",
    "sostenible",
    "sostenibles",
    "compostable",
    "renovable",
    "biodegradable",
)
_USE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("comida_fria", ("comida fria",)),
    (
        "comida_caliente",
        (
            "comida caliente",
            "almuerzo",
            "almuerzos",
            "comida",
            "domicilio",
            "domicilios",
            "portacomida",
            "portacomidas",
        ),
    ),
    (
        "bebida_fria",
        (
            "jugo",
            "jugos",
            "limonada",
            "limonadas",
            "gaseosa",
            "gaseosas",
            "malteada",
            "malteadas",
            "smoothie",
            "smoothies",
            "refresco",
            "refrescos",
            "bebida fria",
            "bebidas frias",
            "helado",
            "frio",
            "fria",
        ),
    ),
    ("sopas", ("sopa", "sopas", "caldo", "caldos")),
    ("salsas", ("salsa", "salsas")),
    ("ensaladas", ("ensalada", "ensaladas")),
    ("frutas", ("fruta", "frutas")),
    ("frituras", ("fritura", "frituras", "papas fritas")),
    ("panaderia", ("pan", "panaderia", "panaderias")),
    ("microondas", ("microondas", "microonda")),
    ("congelacion", ("congelacion", "congelado", "congelar")),
    ("bebida_caliente", ("cafe", "capuchino", "chocolate", "te", "infusion", "bebida caliente")),
)

_CO_CITY_HINTS = (
    "bogota",
    "medellin",
    "cali",
    "barranquilla",
    "bucaramanga",
    "pereira",
    "cartagena",
    "manizales",
    "cucuta",
    "villavicencio",
    "santa marta",
    "ibague",
    "neiva",
    "pasto",
    "armenia",
    "monteria",
    "sincelejo",
    "valledupar",
    "tunja",
    "popayan",
    "tulua",
)
_MX_CITY_HINTS = (
    "mexico",
    "monterrey",
    "guadalajara",
    "tijuana",
    "puebla",
    "queretaro",
    "merida",
    "toluca",
    "leon",
    "juarez",
    "cancun",
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _word_match(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _family(text: str) -> str | None:
    matches: list[tuple[int, str]] = []
    for canonical, words in _FAMILIES:
        for word in words:
            match = re.search(rf"\b{re.escape(word)}\b", text)
            if match:
                matches.append((match.start(), canonical))
    if not matches:
        return None
    return min(matches)[1]


def _capacity(text: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(oz|onzas?|ml)\b", text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "ml":
        return round(value / 29.5735, 2)
    return value


def _quantity(text: str) -> int | None:
    patterns = (
        r"(\d{1,3}(?:[.,]\d{3})+|\d{3,})\s*(?:unidades|unds?|vasos?|platos?|contenedores?|cajas?|piezas?)",
        r"(\d+(?:[.,]\d+)?)\s*mil\b",
        r"unas?\s+(\d{1,3}(?:[.,]\d{3})+|\d{3,})",
        r"necesito\s+(\d{1,3}(?:[.,]\d{3})+|\d{3,})",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(1).replace(".", "").replace(",", "")
        if not raw.isdigit():
            continue
        value = int(raw)
        if "mil" in match.group(0):
            value *= 1000
        return value
    return None


def _city(text: str, cities: tuple[str, ...]) -> str | None:
    for city in cities:
        if _word_match(text, normalize(city)):
            return city
    for hint in _CO_CITY_HINTS:
        if _word_match(text, hint):
            return hint.title()
    for hint in _MX_CITY_HINTS:
        if _word_match(text, hint):
            return hint.title()
    return None


def _country(text: str, city: str | None) -> str | None:
    if "colombia" in text:
        return "CO"
    if "mexico" in text:
        return "MX"
    if city is not None:
        normalized = normalize(city)
        if normalized in _MX_CITY_HINTS:
            return "MX"
        return "CO"
    return None


def _use(text: str) -> str | None:
    for use, words in _USE_PATTERNS:
        if any(_word_match(text, word) for word in words):
            return use
    if _word_match(text, "caliente"):
        return "bebida_caliente"
    return None


def _material(text: str) -> str | None:
    for material in ("ALUMINIO", "PAPEL", "PULPA", "PET", "EPS", "PP", "PS"):
        if _word_match(text, material.lower()):
            return material
    return None


def classify(
    question: str,
    *,
    cities: tuple[str, ...] = (),
    context: str | None = None,
) -> ExtractedQuery:
    """Clasifica la pregunta y extrae atributos comerciales.

    `context` permite resolver seguimientos comerciales ("caliente", "en México")
    cuando la pregunta actual es corta y no trae los atributos.
    """
    current = normalize(question)
    if not current.strip():
        return ExtractedQuery(intent="ambiguous")

    doc_hits_current = sum(1 for keyword in _DOC_KEYWORDS if keyword in current)
    core_current = bool(
        _family(current)
        or any(word in current for word in _PRICE_WORDS)
        or _quantity(current)
        or any(word in current for word in _DISTRIBUTOR_WORDS)
        or _use(current)
        or any(word in current for word in _COMMERCIAL_DESCRIPTORS)
    )
    if doc_hits_current and not core_current:
        return _extracted(current, cities)

    merged = current
    if context and not doc_hits_current:
        merged = f"{current} {normalize(context)}"
    return _extracted(merged, cities)


def _extracted(text: str, cities: tuple[str, ...]) -> ExtractedQuery:
    family = _family(text)
    capacity = _capacity(text)
    quantity = _quantity(text)
    city = _city(text, cities)
    country = _country(text, city)
    use = _use(text)
    temperature = (
        "caliente"
        if _word_match(text, "caliente") or use in {"bebida_caliente", "comida_caliente"}
        else (
            "fria" if _word_match(text, "fria") or use in {"bebida_fria", "comida_fria"} else None
        )
    )
    asks_price = any(word in text for word in _PRICE_WORDS)
    asks_distributor = any(word in text for word in _DISTRIBUTOR_WORDS)
    microwave = _word_match(text, "microondas") or _word_match(text, "microonda")
    freezing = _word_match(text, "congelacion") or _word_match(text, "congelado")
    descriptor = any(word in text for word in _COMMERCIAL_DESCRIPTORS)
    doc_hits = sum(1 for keyword in _DOC_KEYWORDS if keyword in text)
    core_commercial = bool(family or asks_price or quantity or asks_distributor or descriptor)
    weak_commercial = city is not None or country is not None
    if doc_hits and core_commercial:
        if any(_word_match(text, word) for word in ("fabrica", "produce", "hace")):
            intent = "documental"
        else:
            intent = "mixed"
    elif doc_hits:
        intent = "documental"
    elif core_commercial or weak_commercial:
        intent = "commercial"
    else:
        intent = "documental"
    return ExtractedQuery(
        intent=intent,
        family=family,
        capacity_oz=capacity,
        quantity=quantity,
        city=city,
        country=country,
        use=use,
        temperature=temperature,
        material=_material(text),
        prefers_renewable=any(word in text for word in _RENEWABLE_WORDS),
        asks_price=asks_price,
        asks_distributor=asks_distributor,
        microwave=microwave,
        freezing=freezing,
        residual_documental=doc_hits > 0,
    )
