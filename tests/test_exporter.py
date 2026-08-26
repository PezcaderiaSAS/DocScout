"""Pruebas unitarias para DossierBundler y ExporterService (Fase 6)."""

import json
import shutil
from pathlib import Path
import pytest

from docscout.core.models import DocPage, DossierManifest, OfficialSourceMetadata
from docscout.exporter.dossier_bundler import DossierBundler
from docscout.exporter.exporter_service import ExporterService


@pytest.fixture
def sample_pages() -> list[DocPage]:
    p1 = DocPage(
        metadata=OfficialSourceMetadata(
            title="FastAPI First Steps",
            source_url="https://fastapi.tiangolo.com/tutorial/first-steps/",
            domain="fastapi.tiangolo.com",
            tech_stack="fastapi",
            tags=["fastapi", "python"],
            word_count=150,
        ),
        clean_markdown="---\ntitle: \"FastAPI First Steps\"\n---\n\n# First Steps\n\nCreate a `main.py` file with FastAPI.",
    )
    p2 = DocPage(
        metadata=OfficialSourceMetadata(
            title="FastAPI Path Parameters",
            source_url="https://fastapi.tiangolo.com/tutorial/path-params/",
            domain="fastapi.tiangolo.com",
            tech_stack="fastapi",
            tags=["fastapi", "routing"],
            word_count=200,
        ),
        clean_markdown="---\ntitle: \"FastAPI Path Parameters\"\n---\n\n# Path Parameters\n\nYou can declare path parameters with Python format string syntax.",
    )
    return [p1, p2]


def test_dossier_bundler_structure(sample_pages):
    dossier = DossierBundler.build_consolidated_dossier("FastAPI Fundamentals", sample_pages)

    # Validar Frontmatter Global
    assert 'dossier_topic: "FastAPI Fundamentals"' in dossier
    assert "total_sources: 2" in dossier
    assert "total_words: 350" in dossier
    assert 'target_platform: "Google NotebookLM / Gemini"' in dossier

    # Validar Resumen Ejecutivo y Tabla
    assert "## 📊 Resumen Ejecutivo del Lote" in dossier
    assert "| 1 | [FastAPI First Steps](#capitulo-1-fastapi-first-steps)" in dossier
    assert "| 2 | [FastAPI Path Parameters](#capitulo-2-fastapi-path-parameters)" in dossier

    # Validar Capítulos y Anclas
    assert '<a id="capitulo-1-fastapi-first-steps"></a>' in dossier
    assert "## Capítulo 1: FastAPI First Steps" in dossier
    assert '<a id="capitulo-2-fastapi-path-parameters"></a>' in dossier
    assert "## Capítulo 2: FastAPI Path Parameters" in dossier


def test_exporter_service_writes_complete_bundle(sample_pages, tmp_path):
    output_dir = tmp_path / "output_test"

    summary = ExporterService.export_dossier(
        topic="FastAPI Tutorial",
        pages=sample_pages,
        output_root=str(output_dir),
    )

    topic_dir = output_dir / "fastapi-tutorial"
    consolidated_file = topic_dir / "dossier_consolidado.md"
    manifest_file = topic_dir / "manifest.json"
    sources_dir = topic_dir / "sources"

    # Verificar existencia de archivos en disco
    assert topic_dir.is_dir()
    assert consolidated_file.is_file()
    assert manifest_file.is_file()
    assert sources_dir.is_dir()

    # Verificar fuentes individuales
    source_files = list(sources_dir.glob("*.md"))
    assert len(source_files) == 2

    # Verificar contenido del manifest.json
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest = DossierManifest.model_validate(manifest_data)
    assert manifest.topic == "FastAPI Tutorial"
    assert manifest.total_sources == 2
    assert manifest.total_words == 350
    assert len(manifest.sources_summary) == 2
    assert manifest.sources_summary[0]["title"] == "FastAPI First Steps"
