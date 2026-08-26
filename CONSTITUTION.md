# 📜 Constitución del Proyecto: Automatizador de Documentación Oficial (DocScout SDD)
**Versión:** 1.1.0  
**Ámbito:** Validación Obligatoria para Agentes de IA (Antigravity, GitNexus, Ruflo)  
**Idioma de Control:** Español (es-419)

---

## 1. Principio Fundamental (Spec-Driven Development)
> **REGLA DE ORO:** Ningún agente iniciará la escritura de código sin que el usuario haya aprobado previamente el plan o la especificación (`implementation_plan.md` / `.spec`). Toda implementación sin aprobación previa será rechazada e invalidada automáticamente.

---

## 2. Principios Arquitectónicos y Tecnológicos
- **Lenguaje Base:** Python 3.10+ con tipado estricto mediante anotaciones de tipos (`typing`) y validación de esquemas con `pydantic`.
- **Arquitectura en Capas (Clean Architecture):**
  - `CLI / UI`: Interfaz de usuario interactiva por terminal basada en `typer` y `rich`.
  - `Discovery`: Motores de búsqueda agnósticos (DuckDuckGo por defecto, extensible a APIs como Tavily/Google) y filtros heurísticos de dominios oficiales.
  - `Crawler / Fetcher`: Módulos de descarga HTTP resilientes con control de rate limit, User-Agent explícito y reintentos.
  - `Processor / Cleaner`: Limpieza profunda de ruido web (extracción de contenido con `trafilatura` y sanitización con `beautifulsoup4`).
  - `Exporter`: Empaquetador modular y consolidador de dossiers enriquecidos con frontmatter YAML optimizados para Google NotebookLM / Gemini.

---

## 3. Reglas de Calidad y Sanitización de Contenido
- **Cero Ruido Web:** El contenido final Markdown debe estar 100% desprovisto de menús de navegación, barras laterales, avisos de cookies, banners publicitarios y scripts.
- **Preservación Estricta de Código:** Los bloques de código fuente (` ```lang `), tablas y diagramas técnicos deben mantenerse con su identación y estructura exacta sin truncamientos.
- **Metadatos Obligatorios (YAML Frontmatter):** Todo documento o sección exportada debe incluir título canónico, URL fuente oficial, fecha de extracción y palabras clave/etiquetas.

---

## 4. Restricciones y Guardrails de Seguridad
- **Sin Dependencia Forzada de Claves de Pago:** La herramienta debe ser 100% funcional y gratuita de fábrica (DuckDuckGo + Trafilatura/BS4). Las claves de API externas solo se utilizarán si son provistas voluntariamente mediante variables de entorno.
- **Ética de Crawling y Respeto a Servidores:** Respetar pausas mínimas entre peticiones, límites de profundidad (`depth`) y timeouts estrictos para no saturar servidores de documentación oficial.

---

## 5. Protocolo de Verificación del Pipeline
Antes de marcar una tarea como completada, se debe ejecutar:
1. **Pruebas Automatizadas (`/verificar`):** Suite de pruebas en `pytest` cubriendo limpieza de HTML, filtrado de dominios y generación de Markdown/Dossier.
2. **Control de Estilo:** Cumplimiento de estándares PEP 8, formateo limpio y tipado válido.

