# Сервис генерации документов: FastAPI + uvicorn (api:app), порт 8090.
# Шаблоны docx монтируются томом (правка шаблона без пересборки), журнал и стор значений — тоже.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p logs_generated data
ENV GEN_TRACES_DIR=/app/logs_generated GEN_ORG_STORE=/app/data/_org_store.json
EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -sf http://127.0.0.1:8090/api/graph >/dev/null || exit 1
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8090"]
