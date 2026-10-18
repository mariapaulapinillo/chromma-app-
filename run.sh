#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

HOST="${CHROMA_HOST:-172.30.0.183}"
PORT="${CHROMA_PORT:-3020}"

echo "==================================================="
echo "  INICIANDO CHROMA APP - MVP COLORIMETRIA & MAKEUP"
echo "==================================================="

# Python con Flask: el venv del proyecto si existe
PY="python3"
if [ -x ".venv/bin/python" ]; then
  PY="$PWD/.venv/bin/python"
fi

echo "1. Verificando e instalando dependencias..."
"$PY" -m pip install -q -r requirements.txt

echo "2. Inicializando base de datos (chroma.db)..."
"$PY" database.py

echo "3. Iniciando servidor Flask en http://$HOST:$PORT"
CHROMA_HOST="$HOST" CHROMA_PORT="$PORT" exec "$PY" app.py
