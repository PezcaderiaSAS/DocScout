"""Configuración y catálogo de dominios oficiales para DocScout."""

import re
from typing import Dict, List, Set

# Constantes operacionales por defecto (Límites seguros SDD)
DEFAULT_MAX_PAGES: int = 15
DEFAULT_MAX_DEPTH: int = 2
DEFAULT_REQUEST_DELAY: float = 0.5
DEFAULT_TIMEOUT: int = 15
DEFAULT_USER_AGENT: str = "DocScout/1.0 (Official Documentation Extractor for NotebookLM; +https://github.com/docscout)"

# Patrones Regex para detectar subdominios y rutas de documentación oficial
OFFICIAL_DOCS_URL_PATTERNS: List[re.Pattern] = [
    re.compile(r"^https?://docs\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    re.compile(r"^https?://documentation\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    re.compile(r"^https?://[a-zA-Z0-9-]+\.readthedocs\.io", re.IGNORECASE),
    re.compile(r"^https?://[a-zA-Z0-9-]+\.gitbook\.io", re.IGNORECASE),
    re.compile(r"^https?://[a-zA-Z0-9-]+\.dev/(docs|guide|tutorial|learn|reference)", re.IGNORECASE),
    re.compile(r"^https?://[a-zA-Z0-9-]+\.org/(docs|documentation|en/latest|en/stable)", re.IGNORECASE),
    re.compile(r"^https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/(blob|tree)/[a-zA-Z0-9_-]+/docs?", re.IGNORECASE),
]

# Catálogo exhaustivo de más de 60 dominios oficiales verificados organizados por ecosistema
OFFICIAL_DOMAINS_CATALOG: Dict[str, Set[str]] = {
    "python": {
        "docs.python.org",
        "pydantic.dev",
        "docs.pydantic.dev",
        "fastapi.tiangolo.com",
        "sqlmodel.tiangolo.com",
        "flask.palletsprojects.com",
        "docs.djangoproject.com",
        "docs.sqlalchemy.org",
        "requests.readthedocs.io",
        "httpx.readthedocs.io",
        "pytest.org",
        "docs.pytest.org",
        "numpy.org",
        "pandas.pydata.org",
        "scikit-learn.org",
        "pytorch.org",
        "tensorflow.org",
        "docs.celeryq.dev",
        "python-poetry.org",
    },
    "javascript_typescript": {
        "developer.mozilla.org",
        "nodejs.org",
        "typescriptlang.org",
        "react.dev",
        "nextjs.org",
        "vuejs.org",
        "angular.dev",
        "svelte.dev",
        "expressjs.com",
        "nest.js",
        "docs.nestjs.com",
        "tailwindcss.com",
        "vitejs.dev",
        "vitest.dev",
        "bun.sh",
        "deno.land",
        "zod.dev",
        "prisma.io",
        "orm.drizzle.team",
    },
    "frontend_ui_ux_design": {
        "web.dev",
        "developer.mozilla.org",
        "w3.org",
        "patterns.dev",
        "storybook.js.org",
        "m3.material.io",
        "carbondesignsystem.com",
        "radix-ui.com",
        "shadcn.com",
        "ui.shadcn.com",
        "lucide.dev",
        "tremor.so",
        "ant.design",
        "polaris.shopify.com",
        "primer.style",
        "atlassian.design",
        "vercel.com",
        "nngroup.com",
        "smashingmagazine.com",
        "uxdesign.cc",
    },
    "devops_cloud_containers": {
        "docs.docker.com",
        "kubernetes.io",
        "helm.sh",
        "docs.aws.amazon.com",
        "cloud.google.com",
        "learn.microsoft.com",
        "terraform.io",
        "developer.hashicorp.com",
        "ansible.com",
        "docs.ansible.com",
        "nginx.org",
        "prometheus.io",
        "grafana.com",
    },
    "databases": {
        "postgresql.org",
        "dev.mysql.com",
        "mongodb.com",
        "redis.io",
        "sqlite.org",
        "supabase.com",
        "firebase.google.com",
        "neo4j.com",
    },
    "languages_systems": {
        "rust-lang.org",
        "doc.rust-lang.org",
        "go.dev",
        "pkg.go.dev",
        "docs.oracle.com",
        "kotlinlang.org",
        "swift.org",
        "elixir-lang.org",
        "hexdocs.pm",
        "docs.rs",
    },
    "ai_ml_llm": {
        "platform.openai.com",
        "ai.google.dev",
        "docs.anthropic.com",
        "python.langchain.com",
        "docs.llamaindex.ai",
        "huggingface.co",
        "modelcontextprotocol.io",
        "crawl4ai.com",
    },
    "architecture_standards": {
        "patterns.dev",
        "single-spa.js.org",
        "micro-frontends.org",
        "owasp.org",
        "cheatsheetseries.owasp.org",
        "martinfowler.com",
        "12factor.net",
        "auth0.com",
    }
}

# Conjunto consolidado de todos los dominios oficiales planos
ALL_OFFICIAL_DOMAINS: Set[str] = {
    domain
    for domain_group in OFFICIAL_DOMAINS_CATALOG.values()
    for domain in domain_group
}


def is_known_official_domain(domain: str) -> bool:
    """Valida si un dominio está en el catálogo verificado."""
    clean_domain = domain.lower().strip()
    if clean_domain.startswith("www."):
        clean_domain = clean_domain[4:]
    return clean_domain in ALL_OFFICIAL_DOMAINS


def matches_official_pattern(url: str) -> bool:
    """Valida si una URL coincide con patrones heurísticos de documentación oficial."""
    return any(pattern.search(url) for pattern in OFFICIAL_DOCS_URL_PATTERNS)
