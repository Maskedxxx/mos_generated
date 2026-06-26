# -*- coding: utf-8 -*-
"""
Движок сервиса: сессии (копилка значений для наследования) + рендер через реестр.
См. skill mosgen-dev §1.4. Сессии пока in-memory (MVP).
"""
import io
import json
from pathlib import Path

from registry import get_generator

GRAPH_PATH = Path(__file__).resolve().parent / "graph.json"

# session_id -> {key: value} — накопленные значения по сессии (для наследования)
SESSIONS: dict[str, dict] = {}


def get_graph() -> dict:
    """граф документов (UI рисует цепочку и гейтинг)"""
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def get_schema(doc_type: str):
    """схема плейсхолдеров типа (UI рисует форму) или None"""
    g = get_generator(doc_type)
    if not g:
        return None
    return {"doc_type": doc_type, "title": g.TITLE, "fields": g.SCHEMA}


def generate(doc_type: str, session_id: str, values: dict) -> bytes:
    """собрать .docx: подтянуть наследуемые из сессии → сгенерировать → запомнить значения в сессию"""
    g = get_generator(doc_type)
    if not g:
        raise KeyError(doc_type)
    prior = SESSIONS.get(session_id, {})
    merged = dict(values or {})
    # наследование: inherited-поля, не заполненные в форме, тянем из сессии
    for f in g.SCHEMA:
        if f.get("source") == "inherited" and not merged.get(f["key"]) and prior.get(f["key"]):
            merged[f["key"]] = prior[f["key"]]
    doc = g.generate(merged)            # может бросить ValueError при пустых обязательных
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    # запомнить непустые значения в сессию — чтобы поздние доки наследовали
    sess = SESSIONS.setdefault(session_id, {})
    sess.update({k: v for k, v in merged.items() if v not in (None, "")})
    return buf.getvalue()


def session_values(session_id: str) -> dict:
    """накопленные значения сессии"""
    return SESSIONS.get(session_id, {})
