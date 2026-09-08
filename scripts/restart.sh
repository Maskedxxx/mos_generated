#!/bin/bash
# Перезапуск сервиса генерации (uvicorn api:app) в screen-сессии `mosgen`.
# После правок кода — обязателен (uvicorn без --reload). Шаблоны и graph.json читаются
# при каждом запросе, для них перезапуск не нужен.
# Переменные из .env (см. .env.example): GEN_HOST, GEN_PORT, GEN_TRACES_DIR, GEN_ORG_STORE, LOG_DIR.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
GEN_HOST="${GEN_HOST:-0.0.0.0}"; GEN_PORT="${GEN_PORT:-8090}"; LOG_DIR="${LOG_DIR:-/tmp}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
# --- F29: порт должен слушать именно наш процесс (находка 6.5: чужой процесс отвечал 200, а свой умирал) ---
# PID процесса, слушающего TCP-порт $1 (пусто — никто не слушает).
port_pid() { ss -ltnp "sport = :$1" 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2; }
# PID SCREEN-демона сессии с именем $1.
screen_pid() { screen -ls 2>/dev/null | grep -oE "[0-9]+\.$1[[:space:]]" | head -1 | cut -d. -f1; }
# Код 0, если процесс $1 — потомок процесса $2 (подъём по ppid до init).
pid_is_under() { local p="$1"; while [ -n "$p" ] && [ "$p" != "1" ] && [ "$p" != "0" ]; do [ "$p" = "$2" ] && return 0; p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); done; return 1; }
# Порт $1 обязан слушать процесс из screen-сессии $2; иначе сообщение с PID чужого процесса (метка $3) и код 1.
check_port_owner() {
  local lp sp; lp=$(port_pid "$1"); sp=$(screen_pid "$2")
  if [ -z "$lp" ]; then echo "[$3] ОШИБКА: порт $1 никто не слушает" >&2; return 1; fi
  if [ -z "$sp" ] || ! pid_is_under "$lp" "$sp"; then
    echo "[$3] ОШИБКА: порт $1 занят процессом $lp ($(ps -o cmd= -p "$lp" 2>/dev/null | cut -c1-80)) — наш процесс не поднялся, см. лог" >&2
    return 1
  fi
  echo "[$3] порт $1 слушает наш процесс pid=$lp (screen $2)"
}

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
# F29: 200 мог ответить чужой процесс на этом порту — сверяем PID слушателя с нашей screen-сессией.
check_port_owner "$GEN_PORT" "mosgen" "mosgen" || { tail -5 "$LOG_DIR/mosgen.log"; exit 1; }
