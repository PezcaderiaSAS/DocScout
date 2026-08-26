"""Pruebas unitarias para HTMLCleaner y MarkdownBuilder (Fase 3)."""

import pytest
from docscout.processor.html_cleaner import HTMLCleaner
from docscout.processor.markdown_builder import MarkdownBuilder


HTML_SAMPLE_WITH_NOISE = """
<!DOCTYPE html>
<html>
<head>
    <title>FastAPI Tutorial - User Guide</title>
    <script>console.log("tracking script");</script>
    <style>body { background: red; }</style>
</head>
<body>
    <header class="site-header">
        <nav class="navbar">
            <a href="/">Home</a>
            <a href="/docs">Docs</a>
        </nav>
    </header>
    <div id="cookie-consent-banner" class="cookie-banner">
        <p>This site uses cookies. <button>Accept</button></p>
    </div>
    <aside class="sidebar-navigation">
        <ul>
            <li><a href="#intro">Intro</a></li>
            <li><a href="#code">Code</a></li>
        </ul>
    </aside>
    <main role="main" class="docs-content">
        <h1>FastAPI Dependency Injection</h1>
        <p>FastAPI has a very powerful but intuitive <strong>Dependency Injection</strong> system.</p>
        <p>It is designed to be very easy to use, and to make it very easy for any developer to integrate other components with FastAPI.</p>
        
        <h2>Example Code</h2>
        <pre><code class="language-python">from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
</code></pre>

        <h2>Parameters Matrix</h2>
        <table>
            <thead>
                <tr>
                    <th>Parameter</th>
                    <th>Type</th>
                    <th>Default</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>q</td>
                    <td>str</td>
                    <td>None</td>
                </tr>
                <tr>
                    <td>skip</td>
                    <td>int</td>
                    <td>0</td>
                </tr>
            </tbody>
        </table>
    </main>
    <footer class="site-footer">
        <div class="feedback-prompt">Was this page helpful?</div>
        <p>&copy; 2026 FastAPI</p>
    </footer>
</body>
</html>
"""


def test_html_cleaner_removes_scripts_and_noise():
    cleaned = HTMLCleaner.clean_html(HTML_SAMPLE_WITH_NOISE)

    # Verificar que no exista rastro de scripts, estilos, navegación ni cookies
    assert "console.log" not in cleaned
    assert "cookie-consent-banner" not in cleaned
    assert "Was this page helpful?" not in cleaned
    assert "site-header" not in cleaned
    assert "site-footer" not in cleaned

    # Verificar que se preserven los datos técnicos
    assert "FastAPI Dependency Injection" in cleaned
    assert "common_parameters" in cleaned
    assert "<table>" in cleaned


def test_html_cleaner_preserves_code_indentation():
    cleaned = HTMLCleaner.clean_html(HTML_SAMPLE_WITH_NOISE)
    assert "async def common_parameters(q: str = None, skip: int = 0, limit: int = 100):" in cleaned
    assert "return commons" in cleaned


def test_markdown_builder_generates_valid_docpage():
    page = MarkdownBuilder.build_doc_page(
        raw_html=HTML_SAMPLE_WITH_NOISE,
        source_url="https://fastapi.tiangolo.com/tutorial/dependencies/",
        tech_stack="fastapi",
        custom_tags=["dependencies", "backend"],
    )

    # Verificar metadatos canónicos
    assert page.metadata.domain == "fastapi.tiangolo.com"
    assert page.metadata.tech_stack == "fastapi"
    assert "dependencies" in page.metadata.tags
    assert "official-docs" in page.metadata.tags
    assert page.metadata.word_count > 20

    # Verificar estructura YAML Frontmatter y contenido Markdown
    assert page.clean_markdown.startswith("---")
    assert 'title: "FastAPI Dependency Injection"' in page.clean_markdown
    assert 'domain: "fastapi.tiangolo.com"' in page.clean_markdown
    assert "FastAPI Dependency Injection" in page.clean_markdown
    assert "common_parameters" in page.clean_markdown


def test_markdown_builder_fallback_when_empty_trafilatura():
    minimal_html = """
    <html>
        <body>
            <main>
                <h1>Minimal Section</h1>
                <p>Simple description paragraph.</p>
                <pre><code class="language-bash">pip install docscout</code></pre>
            </main>
        </body>
    </html>
    """
    page = MarkdownBuilder.build_doc_page(
        raw_html=minimal_html,
        source_url="https://docs.example.org/install",
        tech_stack="python",
    )

    assert "Minimal Section" in page.clean_markdown
    assert "pip install docscout" in page.clean_markdown
    assert page.metadata.domain == "docs.example.org"
