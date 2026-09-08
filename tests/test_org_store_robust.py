#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты F21: стор ООО не роняет выдачу документа (5.4c) и не теряет записи при гонке (5.4d).
"""
import json
import threading
from pathlib import Path

import pytest

# Полный валидный набор полей акта — генерация должна пройти.
FULL = {
    "org_full": "ООО «Пример»", "org_rep_role_gen": "генерального директора",
    "org_rep_fio_gen": "Тестова Теста Тестовича", "org_rep_role_nom": "Генеральный директор",
    "org_rep_fio_short": "Тестов Т.Т.", "act_date": "«12» марта 2026 г.",
    "agreement_date": "«1» марта 2026 г.", "agreement_num": "№1/2026",
}


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    import engine
    store = tmp_path / "_org_store.json"
    monkeypatch.setattr(engine, "ORG_STORE_PATH", store)
    monkeypatch.setattr(engine, "TRACES_DIR", tmp_path / "logs")
    return engine, store


def test_generate_survives_store_failure(tmp_store, monkeypatch):
    """Падение записи стора не роняет выдачу: generate возвращает валидный .docx."""
    engine, _ = tmp_store

    def _boom(_store):
        raise PermissionError("read-only store")

    monkeypatch.setattr(engine, "_save_org_store", _boom)
    data = engine.generate("akt_nachala", "sess-1", dict(FULL))
    assert isinstance(data, bytes) and data[:2] == b"PK"  # zip-сигнатура docx


def test_concurrent_store_keeps_all_keys(tmp_store):
    """10 параллельных записей с разными ООО → все 10 ключей (блокировка от гонки)."""
    engine, store = tmp_store

    def worker(i):
        engine._store_org_values({"org_full": f"ООО «Парал {i}»", "act_date": f"д{i}"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, 11)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    data = json.loads(Path(store).read_text(encoding="utf-8"))
    assert len(data) == 10, f"ожидалось 10 ключей, получено {len(data)}: {sorted(data)}"
