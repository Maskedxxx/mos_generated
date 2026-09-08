# -*- coding: utf-8 -*-
"""
HTTP API сервиса mos_generated (API-first). Контракт API — docs/ARCHITECTURE.md §2.
Запуск: .venv/bin/uvicorn api:app --host 127.0.0.1 --port 8090
"""
import sys
import threading
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from pydantic import BaseModel

import engine

app = FastAPI(title="mos_generated", description="Сервис генерации документов по шаблонам")


def _traces_retention_job() -> None:
    """F28: очистка журнала генераций по лимиту GEN_TRACES_MAX_GB (самые старые session_* целиком)."""
    try:
        removed = engine.prune_traces()
    except Exception as e:
        print(f"[RETENTION] ошибка очистки журнала: {e}", file=sys.stderr, flush=True)
        return
    if removed:
        names = ", ".join(p.name for p in removed[:5]) + ("…" if len(removed) > 5 else "")
        print(f"[RETENTION] {engine.TRACES_DIR.name}: лимит GEN_TRACES_MAX_GB={engine.TRACES_MAX_GB} ГБ превышен — удалено каталогов: {len(removed)} ({names})", file=sys.stderr, flush=True)


@app.on_event("startup")
def _start_traces_retention() -> None:
    """F28: ротация журнала — сразу при старте (в фоне) и затем раз в сутки."""
    def _loop() -> None:
        while True:
            time.sleep(86400)
            _traces_retention_job()
    threading.Thread(target=_traces_retention_job, daemon=True, name="retention-startup").start()
    threading.Thread(target=_loop, daemon=True, name="retention").start()

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class GenerateRequest(BaseModel):
    """Тело POST /api/types/{doc_type}/generate: session_id (для наследования значений) и values формы."""
    session_id: str = "default"
    values: dict = {}


@app.get("/api/graph")
def graph() -> dict:
    """граф документов — UI рисует цепочку и гейтинг"""
    return engine.get_graph()


@app.get("/api/types/{doc_type}/schema")
def schema(doc_type: str) -> dict:
    """схема плейсхолдеров типа — UI рисует форму"""
    s = engine.get_schema(doc_type)
    if not s:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    return s


@app.post("/api/types/{doc_type}/generate")
def generate(doc_type: str, req: GenerateRequest, request: Request) -> Response:
    """сгенерировать .docx по значениям; значения пишутся в сессию для наследования"""
    try:
        data = engine.generate(doc_type, req.session_id, req.values,
                               client=request.client.host if request.client else None)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return _template_error(doc_type, e)
    return Response(
        content=data,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{doc_type}.docx"'},
    )


def _template_error(doc_type: str, e: Exception) -> JSONResponse:
    """Сбой сборки документа (шаблон повреждён/отсутствует и т.п.) → 500 с текстом вместо пустого
    «Internal Server Error» (аудит устойчивости, находка 5.4e). Исходная ошибка — в technical и в логе."""
    print(f"[generate] {doc_type}: {type(e).__name__}: {e}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Не удалось собрать документ «{doc_type}»: шаблон недоступен или повреждён. Обратитесь к администратору.",
                 "technical": f"{type(e).__name__}: {e}"},
    )


@app.get("/api/types/{doc_type}/download")
def download(doc_type: str, request: Request) -> Response:
    """Нативное скачивание через GET (значения в query): браузер качает .docx сам, без blob/JS."""
    params = dict(request.query_params)
    session_id = params.pop("session_id", "web")
    try:
        data = engine.generate(doc_type, session_id, params,
                               client=request.client.host if request.client else None)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return _template_error(doc_type, e)
    return Response(
        content=data,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{doc_type}.docx"'},
    )


@app.get("/api/orgs")
def orgs() -> list:
    """известные наименования ООО — для подсказок поля ООО"""
    return engine.org_list()


@app.get("/api/org/suggest")
def org_suggest(org: str = "") -> dict:
    """подсказки значений полей по ООО: {field_key: [values]}"""
    return engine.org_suggest(org)


@app.get("/api/session/{session_id}/values")
def session_values(session_id: str) -> dict:
    """накопленные значения сессии (для префилла/наследования)"""
    return engine.session_values(session_id)


import os as _os
@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """собственный веб-фронт генерации (static/index.html)"""
    return FileResponse(_os.path.join(_os.path.dirname(__file__), "static", "index.html"))
