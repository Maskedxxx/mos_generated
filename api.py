# -*- coding: utf-8 -*-
"""
HTTP API сервиса mos_generated (API-first). Контракт — skill mosgen-dev §1.4.
Запуск: .venv/bin/uvicorn api:app --host 127.0.0.1 --port 8090
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel

import engine

app = FastAPI(title="mos_generated", description="Сервис генерации документов по шаблонам")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class GenerateRequest(BaseModel):
    session_id: str = "default"
    values: dict = {}


@app.get("/api/graph")
def graph():
    """граф документов — UI рисует цепочку и гейтинг"""
    return engine.get_graph()


@app.get("/api/types/{doc_type}/schema")
def schema(doc_type: str):
    """схема плейсхолдеров типа — UI рисует форму"""
    s = engine.get_schema(doc_type)
    if not s:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    return s


@app.post("/api/types/{doc_type}/generate")
def generate(doc_type: str, req: GenerateRequest, request: Request):
    """сгенерировать .docx по значениям; значения пишутся в сессию для наследования"""
    try:
        data = engine.generate(doc_type, req.session_id, req.values,
                               client=request.client.host if request.client else None)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=data,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{doc_type}.docx"'},
    )


@app.get("/api/types/{doc_type}/download")
def download(doc_type: str, request: Request):
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
    return Response(
        content=data,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{doc_type}.docx"'},
    )


@app.get("/api/orgs")
def orgs():
    """известные наименования ООО — для подсказок поля ООО"""
    return engine.org_list()


@app.get("/api/org/suggest")
def org_suggest(org: str = ""):
    """подсказки значений полей по ООО: {field_key: [values]}"""
    return engine.org_suggest(org)


@app.get("/api/session/{session_id}/values")
def session_values(session_id: str):
    """накопленные значения сессии (для префилла/наследования)"""
    return engine.session_values(session_id)


import os as _os
@app.get("/", include_in_schema=False)
def index():
    """собственный веб-фронт генерации (static/index.html)"""
    return FileResponse(_os.path.join(_os.path.dirname(__file__), "static", "index.html"))
