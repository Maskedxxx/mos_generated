# -*- coding: utf-8 -*-
"""Стор значений по организациям: нормализация наименования и автоподсказки."""
import engine


def test_normalize_org_same_key_for_spellings():
    """Пять написаний одного ООО (юрформа, кавычки, регистр, пунктуация) дают один ключ стора."""
    variants = ['ООО "Ромашка"', "ооо «Ромашка»", "Ромашка, ООО", "РОМАШКА", "  ромашка ,"]
    keys = {engine.normalize_org(v) for v in variants}
    assert len(keys) == 1 and "ромашка" in keys.pop()


def test_store_and_suggest_roundtrip():
    """Значения формы накапливаются под ООО и возвращаются подсказками; свежие — первыми."""
    engine._store_org_values({"org_full": 'ООО "Ромашка"', "signer_fio": "Иванов И.И.", "empty": ""})
    engine._store_org_values({"org_full": "ооо Ромашка", "signer_fio": "Петров П.П."})
    s = engine.org_suggest("Ромашка")
    assert s["signer_fio"] == ["Петров П.П.", "Иванов И.И."]
    assert "empty" not in s
    assert engine.org_list() == ["ооо Ромашка", 'ООО "Ромашка"']


def test_unknown_org_gives_empty():
    """Неизвестное ООО — пустые подсказки, без ошибки."""
    assert engine.org_suggest("Нет такой") == {}
