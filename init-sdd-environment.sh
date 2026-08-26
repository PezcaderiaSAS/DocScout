#!/usr/bin/env bash

# Configuración de salida en caso de errores
set -e

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0;0m'

echo -e "${BLUE}[1/5] Iniciando validación de pre-requisitos...${NC}"

# 1. Validar herramientas esenciales instaladas en el sistema
for cmd in git node npm; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd no está instalado. Instálalo antes de continuar.${NC}"
        exit 1
    fi
done

# Crear directorio temporal para herramientas de soporte del entorno de agentes
mkdir -p .agents/tools
mkdir -p .agents/skills

# 2. Instalación e integración de GitNexus (Análisis de código AST)
echo -e "${BLUE}[2/5] Descargando y configurando GitNexus Engine...${NC}"
if [ ! -f ".agents/tools/GitNexus/package.json" ]; then
    rm -rf .agents/tools/GitNexus
    git clone https://github.com/abhigyanpatwari/GitNexus.git .agents/tools/GitNexus
    cd .agents/tools/GitNexus
    npm install
    npm run build --if-present || true
    # Crear enlace simbólico local para acceso rápido mediante comandos de barra
    npm link || true
    cd - > /dev/null
else
    echo -e "${YELLOW}GitNexus ya existe en .agents/tools/. Saltando clonación...${NC}"
    cd .agents/tools/GitNexus
    npm link || true
    cd - > /dev/null
fi

# 3. Instalación e integración de Ruflo (Orquestador de enjambres multiagente)
echo -e "${BLUE}[3/5] Descargando y configurando Ruflo Orchestrator...${NC}"
if [ ! -f ".agents/tools/ruflo/package.json" ]; then
    rm -rf .agents/tools/ruflo
    git clone https://github.com/ruvnet/ruflo.git .agents/tools/ruflo
    cd .agents/tools/ruflo
    npm install
    npm run build --if-present || true
    npm link || true
    cd - > /dev/null
else
    echo -e "${YELLOW}Ruflo ya existe en .agents/tools/. Saltando clonación...${NC}"
    cd .agents/tools/ruflo
    npm link || true
    cd - > /dev/null
fi

# 4. Creación automatizada del archivo de reglas e idioma para Antigravity IDE
echo -e "${BLUE}[4/5] Generando manifiesto de comandos de barra y reglas SDD (.antigravityrules)...${NC}"
cat << 'EOF' > .antigravityrules
# Directrices de Desarrollo (Spec-Driven Development)
- Idioma principal de interacción y documentación: Español (es-419).
- Antes de escribir cualquier línea de código, exige una especificación estricta (`constitution` y `specify`).
- Queda estrictamente prohibido realizar modificaciones de código sin un análisis previo de dependencias.

# Comandos de Barra Disponibles (/)
- `/analizar` : Ejecuta el grafo de conocimiento local via `gitnexus analyze`.
- `/enjambre` : Invoca el clúster de agentes de Ruflo para tareas masivas (`ruflo work` o `claude-flow work`).
- `/plan`     : Genera un plan de ingeniería SDD usando la memoria de contexto de ECC.
- `/verificar`: Ejecuta el set de pruebas automatizadas y reporta el análisis de impacto.
- `/optimizar`: Invoca la habilidad especializada de optimización de prompts en formato JSON.
EOF

# Copia de respaldo compatible con clientes basados en ECC clásico
cp .antigravityrules CLAUDE.md

# 5. Inicialización de la estructura Git del proyecto si no existe
echo -e "${BLUE}[5/5] Asegurando consistencia del repositorio local...${NC}"
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}Repositorio Git inicializado.${NC}"
fi

# Evitar que las dependencias de los agentes se suban al repositorio del código web de producción
if ! grep -q ".agents/tools" .gitignore 2>/dev/null; then
    echo -e "\n# Entorno de agentes locales\n.agents/tools/\nnode_modules/" >> .gitignore
fi

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}¡Entorno SDD inicializado con éxito de un solo golpe!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "${YELLOW}Pasos siguientes para el desarrollador:${NC}"
echo -e "1. Ejecuta: ${BLUE}chmod +x init-sdd-environment.sh${NC} (si aún no lo has hecho)"
echo -e "2. Vincula los paquetes de forma interactiva en tu terminal raíz con: ${BLUE}npm link gitnexus ruflo${NC}"
echo -e "3. Abre tu proyecto en Antigravity IDE; las reglas en español y los comandos de barra '/' ya están activos."
