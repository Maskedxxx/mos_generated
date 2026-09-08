# -*- coding: utf-8 -*-
"""Тесты F22/F23: битый шаблон → 500 JSON с текстом; битый стор → .broken-*; типы значений; подписи полей в ошибке."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import sample_values
import api
import engine
from registry import GENERATORS

client = TestClient(api.app, raise_server_exceptions=False)
DT = "akt_nachala"


def test_broken_template_gives_json_500(monkeypatch):
    g = GENERATORS[DT]()

    def _boom(values):
        raise RuntimeError("Package not found at templates/x.docx")

    monkeypatch.setattr(engine, "get_generator", lambda dt: type("G", (), {"SCHEMA": g.SCHEMA, "generate": staticmethod(_boom)})())
    r = client.post(f"/api/types/{DT}/generate", json={"values": sample_values(g.SCHEMA)})
    assert r.status_code == 500
    body = r.json()
    assert "шаблон недоступен или повреждён" in body["detail"] and "Package not found" in body["technical"]


def test_broken_store_renamed(tmp_path, monkeypatch):
    store = tmp_path / "_org_store.json"; store.write_text('{"broken": ', encoding="utf-8")
    monkeypatch.setattr(engine, "ORG_STORE_PATH", store)
    assert engine._load_org_store() == {}
    assert not store.exists()
    broken = list(tmp_path.glob("_org_store.json.broken-*"))
    assert len(broken) == 1 and broken[0].read_text(encoding="utf-8") == '{"broken": '


def test_list_value_is_400_with_label():
    g = GENERATORS[DT]()
    vals = sample_values(g.SCHEMA); vals["agreement_num"] = ["a", "b"]
    r = client.post(f"/api/types/{DT}/generate", json={"values": vals})
    assert r.status_code == 400 and "Номер Соглашения" in r.json()["detail"] and "должно быть текстом" in r.json()["detail"]


def test_number_and_null_are_coerced():
    g = GENERATORS[DT]()
    vals = sample_values(g.SCHEMA); vals["agreement_num"] = 12345; vals["doverennost"] = None
    r = client.post(f"/api/types/{DT}/generate", json={"values": vals})
    assert r.status_code == 200 and r.content[:2] == b"PK"


def test_missing_fields_use_labels():
    r = client.post(f"/api/types/{DT}/generate", json={"values": {}})
    assert r.status_code == 400
    d = r.json()["detail"]
    assert "«Организация (юр.форма + название)»" in d and "org_full" not in d
