# 📋 Especificación Funcional y Técnica (SDD): DocScout
**Código de Especificación:** `SPEC-001-DOCSCOUT-BASE`  
**Versión:** 1.0.0  
**Estado:** Propuesta para Aprobación  
**Autor:** Antigravity AI  
**Idioma:** Español (es-419)  

---

## 1. ¿Por Qué? (Justificación y Problema a Resolver)

### 1.1 El Problema
Al preparar cuadernos especializados en **Google NotebookLM** o alimentar modelos de **Gemini** con documentación técnica:
1. **Ruido Web Excesivo:** La descarga manual o scraping ingenuo de páginas web arrastra menús de navegación, barras laterales, banners publicitarios, rastreadores y avisos de consentimiento de cookies, saturando la ventana de contexto del LLM.
2. **Degradación de Bloques de Código y Tablas:** Muchos extractores genéricos deforman la identación de código fuente, pierden el resaltado de sintaxis o rompen tablas técnicas.
3. **Falta de Trazabilidad:** Los LLMs necesitan conocer la URL canónica de origen, fecha de extracción y versión para evitar alucinaciones temporales.
4. **Fricción Manual:** Descargar 15-30 páginas de una documentación oficial (ej. FastAPI, Docker, Pydantic, React) y unificarlas manualmente es un proceso lento y repetitivo.

### 1.2 La Solución
**DocScout** es un automatizador CLI en Python que localiza fuentes oficiales de tecnologías, rastrea su documentación técnica, aplica limpieza quirúrgica de HTML preservando intactos código y tablas, y empaqueta el contenido en archivos Markdown estructurados con metadatos YAML y dossiers consolidados listos para subir a **Google NotebookLM**.

---

## 2. ¿Qué se va a Construir? (Alcance Funcional)

DocScout es una aplicación de terminal (CLI) interactiva construida en **Python 3.10+** con arquitectura limpia y modular.

### 2.1 Modos de Operación
1. **`docscout search "<término>"`**:
   - Realiza búsquedas mediante DuckDuckGo (sin requerir API keys).
   - Aplica un filtro heurístico de dominios oficiales (ej. `docs.python.org`, `developer.mozilla.org`, `*.dev`, `*.io/docs`, GitHub oficial).
   - Extrae, limpia y compila las mejores fuentes encontradas.
2. **`docscout crawl "<url_raíz>"`**:
   - Inicia desde una URL base oficial (ej. `https://docs.pydantic.dev/latest/`).
   - Descubre y recorre enlaces internos dentro del mismo dominio/ruta hasta agotar `max_pages` (defecto: 15) o `depth` (defecto: 2).
   - Sanitiza y empaqueta cada subpágina.
3. **`docscout interactive`**:
   - Asistente guiado por consola con menús visuales (Rich) para configurar búsquedas, seleccionar páginas a incluir y exportar.
4. **`docscout mcp` (Servidor MCP para Gemini / NotebookLM / Antigravity)**:
   - Inicia el servidor **Model Context Protocol (MCP)** sobre protocolo STDIO (usando FastMCP).
   - Expone la herramienta `search_official_docs` y generación de dossiers directamente a asistentes de IA como Google Gemini, Antigravity y Claude.
   - Genera automáticamente un archivo de configuración listo para importar (`mcp_config.json`).

### 2.2 Pipeline de Procesamiento de Contenido
- **Descarga Resiliente:** Peticiones HTTP con User-Agent formal, reintentos exponenciales y delay ético (0.5s) para respetar los servidores de documentación.
- **Limpieza Quirúrgica:**
  - Trafilatura + BeautifulSoup4 para aislar el contenedor `<main>`, `<article>` o `.markdown-section`.
  - Eliminación total de `<nav>`, `<header>`, `<footer>`, `<aside>`, `<script>`, `<style>`, `<iframe>`, avisos de cookies y botones de feedback.
  - Conversión a Markdown manteniendo bloques ` ```lenguaje `, tablas GFM e hipervínculos relevantes.
- **Generación de Frontmatter YAML:** Metadatos estandarizados al inicio de cada archivo:
  ```yaml
  ---
  title: "FastAPI Dependency Injection"
  source_url: "https://fastapi.tiangolo.com/tutorial/dependencies/"
  extracted_at: "2026-08-26T09:30:00Z"
  domain: "fastapi.tiangolo.com"
  tags: ["fastapi", "python", "backend", "official-docs"]
  ---
  ```

### 2.3 Estructura de Salida Estandarizada
Cada ejecución genera una carpeta en `./output/<slug_del_tema>/` con:
```
output/fastapi_dependencies/
├── dossier_consolidado.md      # Archivo consolidado con índice general para NotebookLM
├── manifest.json               # Metadatos del rastreo, URLs visitadas y estadísticas
└── sources/                    # Fuentes individuales modulares
    ├── 01_intro_dependencies.md
    ├── 02_classes_as_dependencies.md
    └── 03_sub_dependencies.md
```

---

## 3. Casos de Uso y Criterios de Aceptación (Gherkin/BDD)

### Escenario 1: Búsqueda de documentación con filtrado oficial
```gherkin
Dado que el usuario ejecuta: docscout search "Docker multi-stage builds"
Cuando el motor de búsqueda consulta los resultados en DuckDuckGo
Entonces el sistema filtra automáticamente los resultados priorizando dominios oficiales (ej. docs.docker.com)
Y descarga hasta 15 páginas oficiales
Y genera el dossier consolidado en output/docker_multi_stage_builds/dossier_consolidado.md
```

### Escenario 2: Rastreo de documentación por URL raíz
```gherkin
Dado que el usuario ejecuta: docscout crawl "https://docs.pydantic.dev/latest/concepts/models/" --depth 2 --max-pages 10
Cuando el crawler recorre los enlaces internos del mismo subdominio
Entonces se descargan como máximo 10 páginas relacionadas
Y se respeta una pausa de 0.5s entre peticiones
Y se genera la carpeta output/pydantic_models/ con el manifest.json y las fuentes en sources/
```

### Escenario 3: Limpieza profunda de ruido web
```gherkin
Dado un documento HTML oficial que contiene banners de cookies, menús laterales y un bloque de código Python
Cuando el procesador html_cleaner procesa el documento
Entonces el Markdown resultante no contiene rastro de los menús ni cookies
Y el bloque de código Python se preserva intacto con su identación y delimitadores ```python
```

### Escenario 4: Integración MCP para Gemini / Notebooks
```gherkin
Dado que el servidor MCP se encuentra en ejecución con: docscout mcp
Cuando un cliente MCP (Google Gemini / Antigravity / Claude) invoca 'search_official_docs(query="Pydantic custom validators")'
Entonces el servidor busca en dominios oficiales, extrae el Markdown limpio sin ruido
Y devuelve el texto estructurado como respuesta de la herramienta MCP en tiempo real
```

---

## 4. Contratos de Datos (Modelos Pydantic)

### 4.1 Modelo de Página (`DocPage`)
```python
class DocPage(BaseModel):
    url: HttpUrl
    title: str
    raw_html: str
    clean_markdown: str
    extracted_at: datetime
    domain: str
    tags: list[str] = Field(default_factory=list)
    word_count: int
```

### 4.2 Modelo de Configuración de Rastreo (`CrawlConfig`)
```python
class CrawlConfig(BaseModel):
    max_pages: int = Field(default=15, ge=1, le=100)
    max_depth: int = Field(default=2, ge=1, le=5)
    request_delay_seconds: float = Field(default=0.5, ge=0.1, le=5.0)
    timeout_seconds: int = Field(default=15, ge=3, le=60)
    user_agent: str = Field(default="DocScout/1.0 (Official Documentation Extractor for NotebookLM)")
```

### 4.3 Modelo de Manifiesto (`DossierManifest`)
```python
class DossierManifest(BaseModel):
    topic: str
    generated_at: datetime
    total_sources: int
    total_words: int
    sources: list[dict[str, Any]]
```

### 4.4 Esquema de Herramienta MCP (`SearchDocsInput`)
```python
class SearchDocsInput(BaseModel):
    query: str = Field(description="Término técnico o concepto a buscar en fuentes oficiales")
    max_results: int = Field(default=5, ge=1, le=15, description="Número máximo de fuentes oficiales a compilar")
```

---

## 5. Invariantes y Guardrails de Seguridad
1. **0 Claves Obligatorias:** Funciona sin claves de API de pago por defecto.
2. **Aislamiento de Dominio en Crawl:** El crawler no seguirá enlaces que apunten fuera del host de origen de la documentación.
3. **No Ejecución de Código Remoto:** El procesador solo analiza texto y sintaxis Markdown de forma pasiva; ningún script HTML se evalúa.
4. **Sanitización de Nombres de Archivo:** Todos los slugs de archivos se generan sanitizados (`re.sub(r'[^a-zA-Z0-9_-]', '_', title)`).
5. **Compatibilidad MCP Estándar:** Cumplimiento de la especificación oficial MCP 2024-11-05 (JSON-RPC 2.0 sobre STDIO).

---

## 6. Estado de la Especificación
- [x] Responde al **"Por Qué"** (Problema de ruido web y fricción al alimentar NotebookLM).
- [x] Responde al **"Qué"** (CLI interactivo, Crawler/Search, Limpieza profunda, Servidor MCP para Gemini).
- [x] Control de Calidad 1 (`/speckit.clarify`): Ambigüedades de MCP mitigadas.
- [x] Definición de Criterios de Aceptación (Gherkin).
- [x] Contratos de datos tipados (Pydantic).
- [ ] **Aprobación del Usuario (Pendiente de confirmación para iniciar codificación).**
