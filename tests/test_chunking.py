"""Pruebas de la fragmentación del corpus."""

from __future__ import annotations

from assistant.chunking import chunk_corpus, chunk_document
from assistant.corpus import CorpusDocument

BODY = "0123456789" * 250  # 2500 caracteres


def _document(body: str = BODY) -> CorpusDocument:
    return CorpusDocument(
        slug="doc",
        title="Documento",
        url="https://www.carvajal.com/doc",
        section="compania",
        source_type="oficial",
        captured_at="2026-11-01T00:00:00+00:00",
        hash="a" * 64,
        chars=len(body),
        body=body,
    )


def test_fragmentos_tamano_y_solape() -> None:
    # Arrange / Act
    fragments = chunk_document(_document())

    # Assert
    assert len(fragments) == 3
    assert all(len(fragment.text) <= 1000 for fragment in fragments)
    assert fragments[0].text[-200:] == fragments[1].text[:200]
    assert fragments[1].text[-200:] == fragments[2].text[:200]
    assert fragments[-1].char_start == 1600


def test_fragmentos_deterministas_y_metadatos() -> None:
    # Arrange / Act
    first = chunk_document(_document())
    second = chunk_document(_document())

    # Assert
    assert first == second
    assert first[0].slug == "doc"
    assert first[0].url == "https://www.carvajal.com/doc"
    assert [fragment.chunk_index for fragment in first] == [0, 1, 2]


def test_documento_corto_produce_un_fragmento() -> None:
    # Arrange / Act
    fragments = chunk_document(_document("Texto breve sobre Carvajal."))

    # Assert
    assert len(fragments) == 1
    assert fragments[0].char_start == 0


def test_parametros_invalidos() -> None:
    # Arrange / Act / Assert
    try:
        chunk_document(_document(), chunk_size=0)
    except ValueError as error:
        assert "chunk_size" in str(error)
    else:  # pragma: no cover
        raise AssertionError("se esperaba ValueError")
    try:
        chunk_document(_document(), chunk_size=100, overlap=100)
    except ValueError as error:
        assert "overlap" in str(error)
    else:  # pragma: no cover
        raise AssertionError("se esperaba ValueError")


def test_chunk_corpus_ordena_por_slug(documents: list[CorpusDocument]) -> None:
    # Arrange / Act
    fragments = chunk_corpus(documents)

    # Assert
    slugs = [fragment.slug for fragment in fragments]
    assert slugs == sorted(slugs)
