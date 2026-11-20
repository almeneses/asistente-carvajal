"""Pruebas de carga y validación del corpus."""

from __future__ import annotations

from pathlib import Path

import pytest
from assistant.corpus import CorpusError, load_corpus
from tests.conftest import write_document


def test_carga_documentos_del_corpus(gold_dir: Path) -> None:
    # Arrange / Act
    documents = load_corpus(gold_dir)

    # Assert
    assert [document.slug for document in documents] == ["compania", "empaques"]
    assert documents[0].source_type == "oficial"
    assert documents[1].source_type == "tercero"
    assert documents[0].url.startswith("https://")


def test_falta_front_matter(gold_dir: Path) -> None:
    # Arrange
    (gold_dir / "roto.md").write_text("Sin front matter.", encoding="utf-8")
    index_file = gold_dir / "index.jsonl"
    index_file.write_text(
        index_file.read_text(encoding="utf-8") + '{"slug": "roto"}\n',
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(CorpusError, match="front matter"):
        load_corpus(gold_dir)


def test_metadato_obligatorio_ausente(gold_dir: Path) -> None:
    # Arrange
    write_document(
        gold_dir,
        slug="sin-titulo",
        url="https://www.carvajal.com/x",
        title="",
        body="Cuerpo.",
    )
    index_file = gold_dir / "index.jsonl"
    index_file.write_text(
        index_file.read_text(encoding="utf-8") + '{"slug": "sin-titulo"}\n',
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(CorpusError, match="metadatos obligatorios"):
        load_corpus(gold_dir)


def test_slug_ausente_en_indice(gold_dir: Path) -> None:
    # Arrange
    (gold_dir / "index.jsonl").write_text('{"slug": "otro"}\n', encoding="utf-8")

    # Act / Assert
    with pytest.raises(CorpusError, match=r"index\.jsonl"):
        load_corpus(gold_dir)


def test_indice_referencia_documento_ausente(gold_dir: Path) -> None:
    # Arrange
    (gold_dir / "index.jsonl").write_text(
        '{"slug": "compania"}\n{"slug": "empaques"}\n{"slug": "fantasma"}\n',
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(CorpusError, match="ausentes"):
        load_corpus(gold_dir)


def test_corpus_vacio(tmp_path: Path) -> None:
    # Arrange
    directory = tmp_path / "vacio"
    directory.mkdir()
    (directory / "index.jsonl").write_text("", encoding="utf-8")

    # Act / Assert
    with pytest.raises(CorpusError, match="No hay documentos"):
        load_corpus(directory)
