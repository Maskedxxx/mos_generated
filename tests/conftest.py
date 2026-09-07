# -*- coding: utf-8 -*-
"""
Общие фикстуры тестов сервиса генерации.

Журнал трейсов и стор значений по организациям перенаправляются во временный каталог,
чтобы тесты не писали в logs_generated/ и _org_store.json проекта.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import engine  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Каждый тест — со своим журналом, стором ООО и пустыми сессиями."""
    monkeypatch.setattr(engine, "TRACES_DIR", tmp_path / "logs_generated")
    monkeypatch.setattr(engine, "ORG_STORE_PATH", tmp_path / "_org_store.json")
    monkeypatch.setattr(engine, "SESSIONS", {})
    yield


def sample_values(schema: list) -> dict:
    """Заглушки для всех обязательных полей схемы: по ключу подбирается правдоподобное значение."""
    out = {}
    for f in schema:
        if not f.get("required"):
            continue
        k = f["key"]
        if "org" in k and "rep" not in k:
            out[k] = "ООО «Тестовая организация»"
        elif "fio" in k or "responsible" in k:
            out[k] = "Иванов Иван Иванович"
        elif "date" in k:
            out[k] = "«01» сентября 2026 г."
        elif "num" in k:
            out[k] = "№ 1"
        else:
            out[k] = f"тест {k}"
    return out
