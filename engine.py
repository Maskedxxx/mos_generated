# -*- coding: utf-8 -*-
"""
Движок сервиса: сессии (копилка значений для наследования) + рендер через реестр.
Устройство — docs/ARCHITECTURE.md §1. Сессии пока in-memory (MVP).
"""
import io
import json
import os
import shutil
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from registry import get_generator

GRAPH_PATH = Path(__file__).resolve().parent / "graph.json"

# session_id -> {key: value} — накопленные значения по сессии (для наследования)
SESSIONS: dict[str, dict] = {}


# ── Журнал генерации (трейсы) ──
# На каждый вызов generate() пишем каталог-сессию по образцу аудита
# (mos_analiz_refactor: logs_result/<тип>/session_<время>/): чем документ был заполнен,
# что выдали и когда. Без этого нельзя ответить «сколько документов выпущено».
# Путь переопределяется переменной GEN_TRACES_DIR (в Docker — том).
TRACES_DIR = Path(os.getenv("GEN_TRACES_DIR") or Path(__file__).resolve().parent / "logs_generated")
# F28: лимит журнала по объёму (ГБ); 0 — не удалять. Проверяется при старте и раз в сутки (api.py).
TRACES_MAX_GB = float(os.getenv("GEN_TRACES_MAX_GB", "1"))


def _dir_size(path: Path) -> int:
    """Размер каталога в байтах (рекурсивно, без симлинков)."""
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def prune_traces(root: Path | None = None, max_gb: float | None = None) -> list[Path]:
    """
    F28: пока журнал больше лимита — удаляет самые старые каталоги session_* целиком (по mtime).
    root/max_gb по умолчанию — TRACES_DIR / TRACES_MAX_GB; 0 — ничего не удалять. Возвращает удалённые каталоги.
    """
    root = TRACES_DIR if root is None else root
    max_gb = TRACES_MAX_GB if max_gb is None else max_gb
    removed: list[Path] = []
    if max_gb <= 0 or not root.exists():
        return removed
    limit = int(max_gb * 1024 ** 3)
    total = _dir_size(root)
    for p in sorted((p for p in root.glob("*/session_*") if p.is_dir()), key=lambda p: p.stat().st_mtime):
        if total <= limit:
            break
        size = _dir_size(p)
        shutil.rmtree(p, ignore_errors=True)
        total -= size
        removed.append(p)
    return removed


def _write_trace(doc_type: str, session_id: str, values: dict,
                 data: bytes | None = None, error: str | None = None,
                 client: str | None = None) -> None:
    """Пишет трейс одной генерации. Отказ записи НЕ должен ронять выдачу документа."""
    try:
        now = datetime.now()
        stamp = now.strftime('%Y%m%d_%H%M%S_%f')[:-3]
        session_dir = TRACES_DIR / doc_type / f"session_{stamp}"
        # Две генерации в одну миллисекунду (например, документ и сразу повтор) не должны
        # перезаписывать один каталог — добавляем порядковый суффикс.
        n = 1
        while session_dir.exists():
            n += 1
            session_dir = TRACES_DIR / doc_type / f"session_{stamp}_{n}"
        session_dir.mkdir(parents=True)

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
# Путь переопределяется переменной GEN_ORG_STORE (в Docker — том). Каталог создаётся при записи.
ORG_STORE_PATH = Path(os.getenv("GEN_ORG_STORE") or Path(__file__).resolve().parent / "_org_store.json")
_ORG_ANCHOR = "org_full"  # поле-якорь ООО
# Блокировка read-modify-write стора: без неё параллельные generate затирают записи
# друг друга (гонка, 10 параллельных → часть ООО теряется, находка 5.4d).
_ORG_STORE_LOCK = threading.Lock()
_LEGAL_FORMS = {"ооо", "оао", "зао", "ао", "пао", "нао", "ип", "муп", "гуп", "фгуп", "ано", "нко"}


def normalize_org(s: Any) -> str:
    """Максимальная нормализация ООО для матчинга: без юрформы, кавычек, регистра, пунктуации."""
    t = str(s or "").lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)  # кавычки/пунктуация → пробел
    words = [w for w in t.split() if w and w not in _LEGAL_FORMS]
    return " ".join(words)


def _load_org_store() -> dict:
    """
    Назначение: прочитать персистентный стор значений по ООО с диска.
    Вход: нет (путь берётся из ORG_STORE_PATH).
    Выход: dict вида {нормализованное ООО: {field_key: [values...]}}; {} если файла нет.
    Логика: если файл существует — json.loads его содержимого. Битый JSON: файл переименовывается
    в `_org_store.json.broken-<время>` (история не теряется, администратор может восстановить —
    находка 5.4b), пишется строка в лог, возвращается {}. Ошибка чтения (OSError) — {}: стор
    не роняет генерацию.
    """
    if ORG_STORE_PATH.exists():
        try:
            return json.loads(ORG_STORE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            broken = ORG_STORE_PATH.with_name(ORG_STORE_PATH.name + ".broken-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            try:
                ORG_STORE_PATH.replace(broken)
                print(f"[org_store] файл повреждён ({e}); переименован в {broken.name}, стор начат заново")
            except OSError as e2:
                print(f"[org_store] файл повреждён ({e}); переименовать не удалось: {e2}")
            return {}
        except OSError:
            return {}
    return {}


def _save_org_store(store: dict) -> None:
    """
    Назначение: атомарно записать стор значений по ООО на диск.
    Вход: store — dict {нормализованное ООО: {field_key: [values...]}}.
    Выход: None.
    Логика: создаёт каталог ORG_STORE_PATH при необходимости, пишет JSON
    (ensure_ascii=False, indent=2) во временный файл с суффиксом .tmp рядом
    и затем заменяет им целевой файл через Path.replace — частично записанного стора не бывает.
    """
    ORG_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = ORG_STORE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ORG_STORE_PATH)


def _store_org_values(values: dict) -> None:
    """Накопить непустые значения формы в стор под нормализованным ООО (свежие первыми, distinct, до 10)."""
    key = normalize_org(values.get(_ORG_ANCHOR, ""))
    if not key:
        return
    # Чтение-изменение-запись под блокировкой — иначе параллельные вызовы теряют записи (5.4d).
    with _ORG_STORE_LOCK:
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


def get_schema(doc_type: str) -> dict | None:
    """схема плейсхолдеров типа (UI рисует форму) или None"""
    g = get_generator(doc_type)
    if not g:
        return None
    return {"doc_type": doc_type, "title": g.TITLE, "fields": g.SCHEMA}


# ── Проверка значений формы (F23, находки 5.2a, 5.2b) ──
_MISSING_PREFIX = "Не заполнены обязательные поля: "


def _label(g, key: str) -> str:
    """Подпись поля по ключу из SCHEMA генератора (или сам ключ, если поля нет)."""
    for f in g.SCHEMA:
        if f.get("key") == key:
            return f.get("label") or key
    return key


def _normalize_values(g, values: dict) -> dict:
    """
    Назначение: привести значения формы к строкам до подстановки в шаблон.
    Логика: None → "" (поле не заполнено); числа → str; список/словарь — ValueError
    «Поле «<подпись>» должно быть текстом» (раньше в документ попадал Python-repr вроде ['a', 'b']).
    """
    out = {}
    for k, v in values.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (list, dict, tuple, set)):
            raise ValueError(f"Поле «{_label(g, k)}» должно быть текстом")
        elif isinstance(v, bool):
            out[k] = "да" if v else "нет"
        elif isinstance(v, (int, float)):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def _humanize_missing(g, e: ValueError) -> ValueError:
    """«Не заполнены обязательные поля: ['org_full', …]» (ключи из генератора) → подписи полей через схему."""
    text = str(e)
    if not text.startswith(_MISSING_PREFIX):
        return e
    keys = [k for k in re.findall(r"'([^']+)'", text[len(_MISSING_PREFIX):])]
    if not keys:
        return e
    return ValueError(_MISSING_PREFIX + ", ".join(f"«{_label(g, k)}»" for k in keys))


def generate(doc_type: str, session_id: str, values: dict, client: str | None = None) -> bytes:
    """собрать .docx: подтянуть наследуемые из сессии → сгенерировать → запомнить значения в сессию"""
    g = get_generator(doc_type)
    if not g:
        raise KeyError(doc_type)
    prior = SESSIONS.get(session_id, {})
    merged = _normalize_values(g, values or {})
    # наследование: inherited-поля, не заполненные в форме, тянем из сессии
    for f in g.SCHEMA:
        if f.get("source") == "inherited" and not merged.get(f["key"]) and prior.get(f["key"]):
            merged[f["key"]] = prior[f["key"]]
    try:
        doc = g.generate(merged)        # может бросить ValueError при пустых обязательных
    except ValueError as e:
        # «Не заполнены обязательные поля: [ключи]» → подписи полей из схемы (находка 5.2a)
        e = _humanize_missing(g, e)
        _write_trace(doc_type, session_id, merged, error=str(e), client=client)
        raise e
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
    # Накопление в стор ООО не должно ронять выдачу: документ уже собран (правило CLAUDE.md —
    # «журнал не роняет выдачу»; распространяем на стор, находка 5.4c — read-only стор давал 500).
    try:
        _store_org_values(merged)  # накопить значения формы в стор по ООО (персистентно)
    except Exception as e:
        print(f"[org_store] не удалось сохранить значения по ООО: {e}")
    _write_trace(doc_type, session_id, merged, data=data, client=client)
    return data


def session_values(session_id: str) -> dict:
    """накопленные значения сессии"""
    return SESSIONS.get(session_id, {})
