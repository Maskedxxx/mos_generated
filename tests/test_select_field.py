#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты поля выбора в форме генерации: статус Проектного офиса в пункте 1.1 Положения
(обратная связь 14.07 — в шаблоне стояло «(не)является», эксперту нужен выбор).
"""
import pytest
from docx import Document

from registry import get_generator

BASE = {"org_full": "ООО «Ромашка»", "signer_post": "Генеральный директор", "signer_fio": "И.И. Иванов"}


def _statement(doc_path):
    doc = Document(str(doc_path))
    return next(p.text for p in doc.paragraphs if "структурным подразделением предприятия" in p.text)


def test_schema_declares_select_with_options():
    field = next(f for f in get_generator("polozhenie_po").SCHEMA if f["key"] == "po_status")
    assert field["type"] == "select"
    assert field["options"] == ["является", "не является"]
    assert field["default"] == "является" and field["required"] is True


@pytest.mark.parametrize("status", ["является", "не является"])
def test_both_options_land_in_text(tmp_path, status):
    doc = get_generator("polozhenie_po").generate({**BASE, "po_status": status})
    out = tmp_path / "po.docx"
    doc.save(str(out))
    text = _statement(out)
    assert text.startswith(f"Проектный офис (далее - ПО) {status} структурным подразделением")
    assert "(не)" not in text


def test_default_applies_when_value_missing(tmp_path):
    """Поле обязательное, но дефолт из схемы подставляется — форма не падает на пустом значении."""
    doc = get_generator("polozhenie_po").generate(BASE)
    out = tmp_path / "po.docx"
    doc.save(str(out))
    assert "(далее - ПО) является структурным подразделением" in _statement(out)


def test_schema_endpoint_returns_options():
    from fastapi.testclient import TestClient
    import api
    r = TestClient(api.app).get("/api/types/polozhenie_po/schema")
    assert r.status_code == 200
    field = next(f for f in r.json()["fields"] if f["key"] == "po_status")
    assert field["options"] == ["является", "не является"]
