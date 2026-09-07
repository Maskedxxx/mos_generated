# -*- coding: utf-8 -*-
"""
Каждый генератор из реестра: схема валидна, обязательные поля заполнены → получается docx
без незаполненных меток; пустые обязательные → ValueError с перечнем полей.
"""
import io
import re
import zipfile

import pytest

from conftest import sample_values
import engine
from registry import GENERATORS

REQUIRED_FIELD_KEYS = ("key", "label", "type", "required", "source")


@pytest.mark.parametrize("doc_type", sorted(GENERATORS))
def test_schema_valid(doc_type):
    """SCHEMA — список полей с обязательными ключами, уникальными key; TITLE и TEMPLATE заданы, шаблон существует."""
    g = GENERATORS[doc_type]()
    assert g.DOC_TYPE == doc_type
    assert g.TITLE and isinstance(g.TITLE, str)
    from pathlib import Path
    assert Path(g.TEMPLATE).exists(), f"{doc_type}: нет шаблона {g.TEMPLATE}"
    keys = [f["key"] for f in g.SCHEMA]
    assert len(keys) == len(set(keys)), f"{doc_type}: дубликаты key в SCHEMA"
    for f in g.SCHEMA:
        for k in REQUIRED_FIELD_KEYS:
            assert k in f, f"{doc_type}: у поля {f.get('key')} нет {k!r}"
        assert f["source"] in ("own", "inherited"), f"{doc_type}: source={f['source']!r}"


@pytest.mark.parametrize("doc_type", sorted(GENERATORS))
def test_generate_docx_without_leftover_placeholders(doc_type):
    """С заполненными обязательными полями получается валидный docx, в тексте не осталось {{ }}."""
    g = GENERATORS[doc_type]()
    data = engine.generate(doc_type, "test-session", sample_values(g.SCHEMA))
    assert data[:2] == b"PK", f"{doc_type}: не zip/docx"
    z = zipfile.ZipFile(io.BytesIO(data))
    xml = z.read("word/document.xml").decode("utf-8")
    assert "{{" not in xml and "}}" not in xml, f"{doc_type}: в документе остались незаполненные метки"
    assert len(re.sub(r"<[^>]+>", "", xml).strip()) > 100, f"{doc_type}: документ пустой"


@pytest.mark.parametrize("doc_type", sorted(GENERATORS))
def test_missing_required_raises(doc_type):
    """Пустые обязательные поля (без дефолта) → ValueError с перечислением ключей."""
    g = GENERATORS[doc_type]()
    without_default = [f["key"] for f in g.SCHEMA if f.get("required") and "default" not in f]
    if not without_default:
        pytest.skip(f"{doc_type}: все обязательные поля имеют дефолты")
    with pytest.raises(ValueError) as e:
        engine.generate(doc_type, "test-session", {})
    for k in without_default:
        assert k in str(e.value), f"{doc_type}: в ошибке нет поля {k}"


def test_trace_written_on_success_and_error(tmp_path):
    """Журнал: успешная генерация и неудачная попытка оставляют каталог сессии с meta.json."""
    doc_type = sorted(GENERATORS)[0]
    g = GENERATORS[doc_type]()
    engine.generate(doc_type, "s1", sample_values(g.SCHEMA), client="test")
    with pytest.raises(ValueError):
        engine.generate(doc_type, "s1", {})
    sessions = sorted((engine.TRACES_DIR / doc_type).glob("session_*"))
    assert len(sessions) == 2
    import json
    metas = [json.loads((s / "meta.json").read_text(encoding="utf-8")) for s in sessions]
    assert {m["status"] for m in metas} == {"ok", "error"}
    ok = next(m for m in metas if m["status"] == "ok")
    assert ok["client"] == "test" and ok["size_bytes"] > 0
