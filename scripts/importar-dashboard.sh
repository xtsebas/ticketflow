#!/usr/bin/env bash
set -euo pipefail

KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVO="${1:-$RAIZ/monitoring/kibana/dashboard.ndjson}"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe $ARCHIVO" >&2
  exit 1
fi

respuesta="$(curl -fsS -X POST "$KIBANA_URL/api/saved_objects/_import?overwrite=true" -H "kbn-xsrf: true" --form "file=@$ARCHIVO")"
echo "$respuesta"

if ! echo "$respuesta" | grep -q '"success":true'; then
  echo "La importacion reporto errores" >&2
  exit 1
fi
echo "Dashboard importado en $KIBANA_URL"
