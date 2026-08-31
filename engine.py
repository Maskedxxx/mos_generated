# -*- coding: utf-8 -*-
"""
Движок сервиса: сессии (копилка значений для наследования) + рендер через реестр.
См. skill mosgen-dev §1.4. Сессии пока in-memory (MVP).
"""
import io
import json
import re
from datetime import datetime
from pathlib import Path

from registry import get_generator

GRAPH_PATH = Path(__file__).resolve().parent / "graph.json"

# session_id -> {key: value} — накопленные значения по сессии (для наследования)
SESSIONS: dict[str, dict] = {}


# ── Журнал генерации (трейсы) ──
# На каждый вызов generate() пишем каталог-сессию по образцу аудита
# (mos_analiz_refactor: logs_result/<тип>/session_<время>/): чем документ был заполнен,
# что выдали и когда. Без этого нельзя ответить «сколько документов выпущено».
TRACES_DIR = Path(__file__).resolve().parent / "logs_generated"


def _write_trace(doc_type: str, session_id: str, values: dict,
                 data: bytes | None = None, error: str | None = None,
                 client: str | None = None) -> None:
    """Пишет трейс одной генерации. Отказ записи НЕ должен ронять выдачу документа."""
    try:
        now = datetime.now()
        session_dir = TRACES_DIR / doc_type / f"session_{now.strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        session_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{doc_type}.docx"
        meta = {
            "timestamp": now.isoformat(timespec="seconds"),
            "doc_type": doc_type,
            "session_id": session_id,
            "client": client,
            "status": "ok" if error is None else "error",
            "filename": filename if data else None,
            "size_bytes": len(data) if data else None,
            "error": error,
        }
        (session_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (session_dir / "values.json").write_text(
            json.dumps(values or {}, ensure_ascii=False, indent=2), encoding="utf-8")
        if data:
            (session_dir / filename).write_bytes(data)
    except Exception as e:  # журнал не критичен для пользователя — документ важнее
        print(f"[trace] не удалось записать трейс генерации {doc_type}: {e}")


# ── Персистентный стор значений по ООО (автозаполнение) ──
# Ключ — нормализованное наименование ООО; значение — {field_key: [values...]} (свежие первыми).
ORG_STORE_PATH = Path(__file__).resolve().parent / "_org_store.json"
_ORG_ANCHOR = "org_full"  # поле-якорь ООО
_LEGAL_FORMS = {"ооо", "оао", "зао", "ао", "пао", "нао", "ип", "муп", "гуп", "фгуп", "ано", "нко"}


def normalize_org(s) -> str:
    """Максимальная нормализация ООО для матчинга: без юрформы, кавычек, регистра, пунктуации."""
    t = str(s or "").lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)  # кавычки/пунктуация → пробел
    words = [w for w in t.split() if w and w not in _LEGAL_FORMS]
    return " ".join(words)


def _load_org_store() -> dict:
    if ORG_STORE_PATH.exists():
        try:
            return json.loads(ORG_STORE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_org_store(store: dict) -> None:
    tmp = ORG_STORE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ORG_STORE_PATH)


def _store_org_values(values: dict) -> None:
    """Накопить непустые значения формы в стор под нормализованным ООО (свежие первыми, distinct, до 10)."""
    key = normalize_org(values.get(_ORG_ANCHOR, ""))
    if not key:
        return
    store = _load_org_store()
    bucket = store.setdefault(key, {})
    for k, v in values.items():
        if v in (None, ""):
            continue
        lst = bucket.setdefault(k, [])
        if v in lst:
            lst.remove(v)
        lst.insert(0, v)
        del lst[10:]
    _save_org_store(store)


def org_suggest(org_raw: str) -> dict:
    """Подсказки значений полей по ООО: {field_key: [values...]} или {} если ООО неизвестно."""
    return _load_org_store().get(normalize_org(org_raw), {})


def org_list() -> list:
    """Известные наименования ООО (для подсказок самого поля ООО), distinct, свежие первыми."""
    store = _load_org_store()
    seen, out = set(), []
    for bucket in store.values():
        for o in bucket.get(_ORG_ANCHOR, []):
            if o not in seen:
                seen.add(o)
                out.append(o)
    return out



def get_graph() -> dict:
    """граф документов (UI рисует цепочку и гейтинг)"""
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def get_schema(doc_type: str):
    """схема плейсхолдеров типа (UI рисует форму) или None"""
    g = get_generator(doc_type)
    if not g:
        return None
    return {"doc_type": doc_type, "title": g.TITLE, "fields": g.SCHEMA}


def generate(doc_type: str, session_id: str, values: dict, client: str | None = None) -> bytes:
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
    try:
        doc = g.generate(merged)        # может бросить ValueError при пустых обязательных
    except Exception as e:
        # неудачную попытку тоже журналируем: видно, сколько раз документ не удалось получить
        _write_trace(doc_type, session_id, merged, error=str(e), client=client)
        raise
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    data = buf.getvalue()
    # запомнить непустые значения в сессию — чтобы поздние доки наследовали
    sess = SESSIONS.setdefault(session_id, {})
    sess.update({k: v for k, v in merged.items() if v not in (None, "")})
    _store_org_values(merged)  # накопить значения формы в стор по ООО (персистентно)
    _write_trace(doc_type, session_id, merged, data=data, client=client)
    return data


def session_values(session_id: str) -> dict:
    """накопленные значения сессии"""
    return SESSIONS.get(session_id, {})
