# -*- coding: utf-8 -*-
"""
HTTP API сервиса mos_generated (API-first). Контракт — skill mosgen-dev §1.4.
Запуск: .venv/bin/uvicorn api:app --host 127.0.0.1 --port 8090
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
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
def generate(doc_type: str, req: GenerateRequest):
    """сгенерировать .docx по значениям; значения пишутся в сессию для наследования"""
    try:
        data = engine.generate(doc_type, req.session_id, req.values)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"неизвестный тип: {doc_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=data,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{doc_type}.docx"'},
    )


@app.get("/api/session/{session_id}/values")
def session_values(session_id: str):
    """накопленные значения сессии (для префилла/наследования)"""
    return engine.session_values(session_id)
