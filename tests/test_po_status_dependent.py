# -*- coding: utf-8 -*-
"""
Зависимые поля 3.5 (решение владельца 29.09): в приказе о формировании ПО выбор «является / не является»
структурным подразделением. При «не является» п.3 (штатное расписание и ДИ) и п.4 (штатное расписание и
оргструктура) не требуются: поля неактивны (required_if), в документе — прочерк, пункты остаются.
"""
import io

import pytest
from docx import Document

import engine
from conftest import sample_values
from registry import GENERATORS

DOC = "prikaz_formirovanie_po"
DEPENDENT = ("resp3", "srok3", "resp4", "srok4")


def _values(**over):
    v = sample_values(GENERATORS[DOC]().SCHEMA)
    v.update(over)
    return v


def _items(data: bytes) -> dict:
    """Абзацы п.3 и п.4 (строки «Ответственный … срок …» сразу после поручений про штатное расписание)."""
    paras = [p.text for p in Document(io.BytesIO(data)).paragraphs]
    out = {}
    for i, t in enumerate(paras):
        if t.startswith("Разработать проект штатного расписания"):
            out["p3"] = paras[i + 1]
        if t.startswith("Внести изменение в штатное расписание"):
            out["p4"] = paras[i + 1]
    return out


def test_schema_status_select_and_dependent_fields():
    schema = {f["key"]: f for f in GENERATORS[DOC]().SCHEMA}
    st = schema["po_status"]
    assert st["type"] == "select" and st["options"] == ["является", "не является"] and st["default"] == "является"
    for k in DEPENDENT:
        assert schema[k]["required_if"] == {"po_status": "является"}
    # остальные поля без условия
    assert all("required_if" not in f for k, f in schema.items() if k not in DEPENDENT)


def test_structural_requires_dependent_fields():
    """«является» (и по умолчанию): п.3/п.4 обязательны, как раньше."""
    v = _values(po_status="является")
    for k in DEPENDENT:
        v.pop(k)
    with pytest.raises(ValueError) as e:
        engine.generate(DOC, "t", v)
    for k in DEPENDENT:
        label = next(f["label"] for f in GENERATORS[DOC]().SCHEMA if f["key"] == k)
        assert label in str(e.value)


def test_not_structural_generates_without_dependent_fields():
    v = _values(po_status="не является")
    for k in DEPENDENT:
        v.pop(k)
    items = _items(engine.generate(DOC, "t", v))
    assert items["p3"] == "Ответственный _______________ срок ______________."
    assert items["p4"] == "Ответственный _______________ срок ______________."


def test_not_structural_ignores_stale_values():
    """Старые значения (например, подставленные по ООО) при «не является» в документ не попадают."""
    v = _values(po_status="не является", resp3="Гл. бухгалтер Петров П.П.", srok3="06.06.2026")
    items = _items(engine.generate(DOC, "t", v))
    assert "Петров" not in items["p3"] and "06.06.2026" not in items["p3"]


def test_structural_values_land_in_document():
    v = _values(po_status="является", resp3="Гл. бухгалтер Петров П.П.", srok3="06.06.2026",
                resp4="Начальник ОК Иванов И.И.", srok4="07.06.2026")
    items = _items(engine.generate(DOC, "t", v))
    assert items["p3"] == "Ответственный Гл. бухгалтер Петров П.П. срок 06.06.2026."
    assert items["p4"] == "Ответственный Начальник ОК Иванов И.И. срок 07.06.2026."


def test_default_status_keeps_old_api_behaviour():
    """Клиент API без po_status получает прежнее поведение (статус по умолчанию «является»)."""
    v = _values()
    v.pop("po_status", None)
    items = _items(engine.generate(DOC, "t", v))
    assert "_____" not in items["p3"]


def test_schema_endpoint_returns_required_if():
    from fastapi.testclient import TestClient
    import api
    r = TestClient(api.app).get(f"/api/types/{DOC}/schema")
    assert r.status_code == 200
    f = {x["key"]: x for x in r.json()["fields"]}
    assert f["resp3"]["required_if"] == {"po_status": "является"}
