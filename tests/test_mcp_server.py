"""Pruebas unitarias para el Servidor MCP y generador de configuración (Fase 7)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from docscout.core.models import DocPage, OfficialSourceMetadata, SearchResultItem
from docscout.mcp.config_generator import MCPConfigGenerator
from docscout.mcp.server import crawl_and_export_docs, mcp, search_official_docs


def test_mcp_server_initialization():
    assert mcp.name == "DocScout"


def test_mcp_config_generator(tmp_path):
    config = MCPConfigGenerator.generate_config(
        python_path="/custom/bin/python",
        project_root="/custom/project",
    )

    assert "mcpServers" in config
    assert "docscout" in config["mcpServers"]
    server_def = config["mcpServers"]["docscout"]
    assert server_def["command"] == "/custom/bin/python"
    assert server_def["args"] == ["-m", "docscout.mcp.server"]
    assert "PYTHONPATH" in server_def["env"]

    # Probar exportación a archivo
    out_file = tmp_path / "mcp_config.json"
    exported_path = MCPConfigGenerator.export_config_file(
        output_file=str(out_file),
        project_root="/custom/project",
        python_path="/custom/bin/python",
    )
    assert Path(exported_path).is_file()
    loaded_data = json.loads(Path(exported_path).read_text(encoding="utf-8"))
    assert loaded_data["mcpServers"]["docscout"]["command"] == "/custom/bin/python"


@patch("docscout.mcp.server.SearchEngine.search")
@patch("docscout.mcp.server.PageFetcher.fetch")
def test_search_official_docs_tool(mock_fetch, mock_search):
    mock_search.return_value = [
        SearchResultItem(
            title="FastAPI Background Tasks",
            url="https://fastapi.tiangolo.com/tutorial/background-tasks/",
            snippet="Background tasks guide",
            is_official_domain=True,
            confidence_score=1.0,
        )
    ]
    mock_fetch.return_value = """
    <html>
        <body>
            <main>
                <h1>Background Tasks</h1>
                <p>You can define background tasks in FastAPI easily.</p>
                <pre><code class="language-python">def write_notification(email: str, message=""): pass</code></pre>
            </main>
        </body>
    </html>
    """

    result_md = search_official_docs(query="FastAPI background tasks", max_results=1)

    assert "Background Tasks" in result_md
    assert "write_notification" in result_md
    assert "fastapi.tiangolo.com" in result_md
    assert "---" in result_md


@patch("docscout.mcp.server.SearchEngine.search")
def test_search_official_docs_no_results(mock_search):
    mock_search.return_value = []
    result = search_official_docs(query="NonExistentTechXYZ123")
    assert "Sin resultados oficiales" in result


@patch("docscout.mcp.server.SitemapCrawler.crawl")
@patch("docscout.mcp.server.ExporterService.export_dossier")
def test_crawl_and_export_docs_tool(mock_export, mock_crawl):
    mock_page = DocPage(
        metadata=OfficialSourceMetadata(
            title="Pydantic Basics",
            source_url="https://docs.pydantic.dev/latest/",
            domain="docs.pydantic.dev",
            word_count=100,
        ),
        clean_markdown="# Pydantic Basics",
    )
    mock_crawl.return_value = [mock_page]
    mock_export.return_value = {
        "sources_count": 1,
        "total_words": 100,
        "consolidated_file": "/path/to/dossier_consolidado.md",
        "manifest_file": "/path/to/manifest.json",
    }

    response = crawl_and_export_docs(
        url="https://docs.pydantic.dev/latest/",
        topic="Pydantic",
        max_pages=5,
    )

    assert "Dossier generado exitosamente para **Pydantic**" in response
    assert "dossier_consolidado.md" in response
