# 🛰️ DocScout: Extractor y Curador Inteligente de Documentación Oficial

**DocScout** es un motor CLI y servidor MCP (*Model Context Protocol*) diseñado para desarrolladores y agentes de IA. Busca, filtra, sanitiza y descarga automáticamente documentación técnica oficial desde fuentes verificadas, empaquetándola en dossiers optimizados para **Google NotebookLM**, **Google Gemini**, y modelos LLM avanzados.

---

## 🌟 Características Principales

- **Filtro de Fuentes Oficiales y Scoring:** Catálogo de +60 dominios oficiales (Docker, Python, React, FastAPI, AWS, GCP, etc.) y descarte automático de sitios agregadores o contenido de baja calidad.
- **Limpieza Quirúrgica HTML:** Algoritmo basado en *BeautifulSoup4* y *Trafilatura* que remueve scripts, navbars, footers, avisos de cookies y banners, preservando bloques de código `pre/code`, tablas y formateo técnico.
- **Formato NotebookLM Ready:** Generación de frontmatter YAML canónico, metadatos y un `dossier_consolidado.md` con tabla de contenidos (TOC) navegable para alimentar cuadernos de NotebookLM.
- **Servidor MCP Nativo (FastMCP):** Expone herramientas (`search_official_docs`, `crawl_and_export_docs`) sobre protocolo STDIO / JSON-RPC 2.0 para agentes como Gemini, Claude y Antigravity.
- **CLI Interactivo:** Interfaz visual con soporte para spinners, barras de progreso y tablas informativas mediante *Rich* y *Typer*.

---

## 📦 Requisitos e Instalación

### Requisitos Previos
- **Python 3.10+** (probado en Python 3.13)
- **Git**

### Instalación

1. Clonar el repositorio o posicionarse en el directorio del proyecto:
   ```bash
   cd DocumentacionesOficiales
   ```

2. Crear y activar un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Instalar en modo editable:
   ```bash
   pip install -e .
   ```

---

## 🚀 Guía de Uso del CLI

### 1. Búsqueda y Extracción por Término
Busca en la web técnica, filtra por fuentes oficiales y genera el dossier:
```bash
python -m docscout search "Docker multi-stage builds" --max-results 3
```

Opciones:
- `--max-results, -n`: Número máximo de fuentes oficiales a extraer (por defecto: `5`).
- `--output-dir, -o`: Directorio de destino para los archivos (por defecto: `output/`).

### 2. Rastreo de Documentación por URL Raíz
Rastrea un sitio de documentación respetando límites de profundidad y dominio:
```bash
python -m docscout crawl "https://docs.docker.com/build/building/multi-stage/" --max-pages 5 --max-depth 2
```

Opciones:
- `--max-pages, -p`: Límite máximo de páginas a descargar (por defecto: `15`).
- `--max-depth, -d`: Profundidad máxima de enlaces internos (por defecto: `2`).
- `--delay`: Retardo en segundos entre peticiones (por defecto: `0.5s`).

### 3. Asistente Interactivo
Modo guiado paso a paso en la terminal:
```bash
python -m docscout interactive
```

### 4. Servidor MCP para Agentes de IA
Inicia el servidor Model Context Protocol en modo STDIO:
```bash
python -m docscout mcp
```

Para generar la configuración de integración MCP:
```bash
python -m docscout mcp --generate-config
```

---

## 🔌 Integración con Google Gemini / Antigravity / Claude

Para conectar DocScout como servidor de contexto en tu cliente MCP (ej. `antigravity`, `Claude Desktop` o `Gemini`):

Añade en tu archivo `mcp_config.json`:
```json
{
  "mcpServers": {
    "docscout": {
      "command": "python",
      "args": ["-m", "docscout", "mcp"],
      "env": {}
    }
  }
}
```

### Herramientas Expuestas:
- `search_official_docs(query, max_results)`: Busca y extrae documentación oficial relevante directamente al contexto del LLM.
- `crawl_and_export_docs(start_url, max_pages, max_depth)`: Rastrea y consolida documentación técnica completa.

---

## 📓 Cómo Importar en Google NotebookLM

1. Tras ejecutar `docscout search` o `docscout crawl`, navega a la carpeta generada en `output/<tema-slug>/`.
2. Abre [Google NotebookLM](https://notebooklm.google.com/).
3. Crea un nuevo cuaderno o abre uno existente.
4. En la sección **Fuentes** (*Sources*):
   - **Opción A (Recomendada):** Sube el archivo único `dossier_consolidado.md`.
   - **Opción B:** Sube los archivos individuales dentro del directorio `sources/`.
5. ¡Listo! NotebookLM tendrá acceso al 100% de la documentación técnica oficial sin ruido de interfaz, headers ni publicidades.

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración:

```bash
pytest tests/ -v
```

Cobertura de pruebas:
- Limpieza HTML y aislamiento de contenedores semánticos (`tests/test_cleaner.py`).
- Algoritmo de filtrado de dominios y búsqueda técnica (`tests/test_discovery.py`).
- Generación de dossiers y manifiestos NotebookLM (`tests/test_exporter.py`).
- Inicialización y llamadas a herramientas del servidor MCP (`tests/test_mcp_server.py`).

---

## ⚖️ Licencia y Directrices

Desarrollado bajo principios de **Spec-Driven Development (SDD)**. Consulte [CONSTITUTION.md](CONSTITUTION.md) y [TASKS.md](TASKS.md) para más detalles sobre estándares de arquitectura y gobernanza del proyecto.
