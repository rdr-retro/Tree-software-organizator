#!/bin/bash

# Script para ejecutar Tree Software Organization
# Crea un entorno virtual, instala dependencias y ejecuta el programa

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=== Tree Software Organization ==="
echo ""

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual..."
    /opt/homebrew/bin/python3.12 -m venv "$VENV_DIR"
    echo ""
fi

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

# Verificar si PySide6 está instalado
if ! python -c "import PySide6" 2>/dev/null; then
    echo "Instalando PySide6..."
    pip install PySide6
    echo ""
fi

# Ejecutar el programa
echo "Ejecutando Tree Software Organization..."
echo ""
python "$SCRIPT_DIR/src/tree_software_organization.py"

# Desactivar entorno virtual
deactivate
