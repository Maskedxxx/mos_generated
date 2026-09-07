# -*- coding: utf-8 -*-
"""HTTP API сервиса генерации через TestClient: граф, схема, скачивание, подсказки."""
import pytest
from fastapi.testclient import TestClient

from conftest import sample_values
import api
from registry import GENERATORS

client = TestClient(api.app)


def test_graph_lists_all_generators():
    """/api/graph отдаёт узлы для каждого зарегистрированного типа."""
    r = client.get("/api/graph")
    assert r.status_code == 200
    nodes = {n["doc_type"] for n in r.json()["nodes"]}
    assert set(GENERATORS) <= nodes, f"в graph.json нет узлов: {set(GENERATORS) - nodes}"


@pytest.mark.parametrize("doc_type", sorted(GENERATORS)[:3])
def test_schema_endpoint(doc_type):
    """/api/types/{тип}/schema — title и поля формы."""
    r = client.get(f"/api/types/{doc_type}/schema")
    assert r.status_code == 200
    body = r.json()
    assert body["doc_type"] == doc_type and body["title"] and body["fields"]


def test_schema_unknown_type_404():
    assert client.get("/api/types/no_such_type/schema").status_code == 404


def test_download_requires_fields_then_returns_docx():
    """/download: без обязательных — 400 с перечнем; с заполненными — docx."""
    doc_type = sorted(GENERATORS)[0]
    g = GENERATORS[doc_type]()
    r = client.get(f"/api/types/{doc_type}/download", params={"session_id": "t"})
    assert r.status_code == 400 and "обязательные" in r.json()["detail"]
    r = client.get(f"/api/types/{doc_type}/download", params={**sample_values(g.SCHEMA), "session_id": "t"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert r.content[:2] == b"PK"


def test_org_suggest_after_generate():
    """После генерации значения доступны через /api/orgs и /api/org/suggest."""
    doc_type = sorted(GENERATORS)[0]
    g = GENERATORS[doc_type]()
    values = sample_values(g.SCHEMA)
    assert client.post(f"/api/types/{doc_type}/generate", json={"session_id": "s", "values": values}).status_code == 200
    assert values["org_full"] in client.get("/api/orgs").json()
    assert client.get("/api/org/suggest", params={"org": "тестовая организация"}).json()["org_full"] == [values["org_full"]]
