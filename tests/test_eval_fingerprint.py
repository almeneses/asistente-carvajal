"""Pruebas del fingerprint del corpus."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from assistant.evaluation.fingerprint import (
    corpus_fingerprint,
    fingerprints,
    index_jsonl_sha256,
    is_stale,
)
from tests.eval_fixtures import sample_documents


def test_fingerprint_es_determinista() -> None:
    # Arrange
    documents = sample_documents()

    # Act
    first = corpus_fingerprint(documents)
    second = corpus_fingerprint(list(reversed(documents)))

    # Assert
    assert first == second
    assert len(first) == 64


def test_fingerprint_cambia_si_cambia_un_documento() -> None:
    # Arrange
    documents = sample_documents()
    changed = list(documents)
    changed[0] = replace(documents[0], hash="b" * 64)

    # Act / Assert
    assert corpus_fingerprint(documents) != corpus_fingerprint(changed)


def test_index_jsonl_sha256(tmp_path: Path) -> None:
    # Arrange
    index_file = tmp_path / "index.jsonl"
    content = '{"slug": "compania"}\n'
    index_file.write_text(content, encoding="utf-8")

    # Act
    digest = index_jsonl_sha256(index_file)

    # Assert
    assert digest == sha256(content.encode()).hexdigest()


def test_fingerprints_y_estado_obsoleto(tmp_path: Path) -> None:
    # Arrange
    documents = sample_documents()
    index_file = tmp_path / "index.jsonl"
    index_file.write_text("{}\n", encoding="utf-8")

    # Act
    payload = fingerprints(documents, index_file)

    # Assert
    assert payload["corpus_fingerprint"] == corpus_fingerprint(documents)
    assert is_stale(payload["corpus_fingerprint"], documents) is False
    assert is_stale("otro-fingerprint", documents) is True
