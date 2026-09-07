#!/bin/bash
# Перезапуск сервиса генерации (uvicorn api:app) в screen-сессии `mosgen`.
# После правок кода — обязателен (uvicorn без --reload). Шаблоны и graph.json читаются
# при каждом запросе, для них перезапуск не нужен.
# Переменные из .env (см. .env.example): GEN_HOST, GEN_PORT, GEN_TRACES_DIR, GEN_ORG_STORE, LOG_DIR.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
GEN_HOST="${GEN_HOST:-0.0.0.0}"; GEN_PORT="${GEN_PORT:-8090}"; LOG_DIR="${LOG_DIR:-/tmp}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
[ -x "$PYTHON" ] || { echo "[mosgen] нет интерпретатора $PYTHON — создайте venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2; exit 1; }
screen -S mosgen -X quit 2>/dev/null || true
sleep 1
screen -dmS mosgen bash -c "cd '$ROOT'; if [ -f ./.env ]; then set -a; . ./.env; set +a; fi; exec '$PYTHON' -m uvicorn api:app --host '$GEN_HOST' --port '$GEN_PORT' >> '$LOG_DIR/mosgen.log' 2>&1"
code=""
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$GEN_PORT/api/graph" 2>/dev/null || true)
  if [ "$code" = "200" ]; then break; fi
  sleep 1
done
echo "[mosgen] http://$GEN_HOST:$GEN_PORT/api/graph -> ${code:-нет ответа}  (лог: $LOG_DIR/mosgen.log)"
if [ "$code" != "200" ]; then tail -5 "$LOG_DIR/mosgen.log"; exit 1; fi
