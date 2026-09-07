#!/bin/bash
# Проверка сервиса генерации: список типов отвечает, шаблоны на месте.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
GEN_PORT="${GEN_PORT:-8090}"
n=$(curl -s --max-time 5 "http://127.0.0.1:$GEN_PORT/api/graph" | "${PYTHON:-$ROOT/.venv/bin/python}" -c 'import sys,json;print(len(json.load(sys.stdin)["nodes"]))' 2>/dev/null)
if [ -n "$n" ]; then echo "[health] mosgen :$GEN_PORT -> ok, типов: $n, шаблонов: $(ls "$ROOT"/templates/*.docx 2>/dev/null | wc -l | tr -d ' ')"; exit 0
else echo "[health] mosgen :$GEN_PORT -> НЕ ОТВЕЧАЕТ"; exit 1; fi
