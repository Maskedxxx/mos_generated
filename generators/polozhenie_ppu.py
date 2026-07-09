# -*- coding: utf-8 -*-
"""
Генератор документа «Положение о системе подачи и реализации ППУ» (doc_type=polozhenie_ppu).

Контракт (skill mosgen-dev §1.1). Эталон — канонический образец заказчика
«ПРИМЕР №3 ООО Содекс»: тело Положения — фиксированный методический регламент
(разделы, формы, гриф УТВЕРЖДАЮ), без наименования организации. Единственное
переменное место — привязка к родительскому приказу в шапке T0
(«Приложение №1 к приказу от <дата> №<номер>»). Плейсхолдеры самодостаточные.
"""
from pathlib import Path

try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PolozheniePpu:
    DOC_TYPE = "polozhenie_ppu"
    TITLE = "Положение о системе подачи и реализации ППУ"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "polozhenie_ppu.docx")

    # Плейсхолдеры: только привязка к приказу (тело — фиксированный регламент).
    SCHEMA = [
        {"key": "prikaz_date", "label": "Дата приказа (Положение — Приложение №1 к нему)", "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "prikaz_num",  "label": "Номер приказа",                                   "type": "text", "required": True, "source": "own", "hint": "12-ПТ"},
    ]

    def defaults(self) -> dict:
        return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}

    def context(self, values: dict) -> dict:
        ctx = self.defaults()
        ctx.update({k: v for k, v in (values or {}).items() if v not in (None, "")})
        return ctx

    def generate(self, values: dict):
        ctx = self.context(values)
        missing = [f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None:
            raise RuntimeError("docxtpl не установлен (нужен в venv сервиса)")
        doc = DocxTemplate(self.TEMPLATE)
        doc.render(ctx)
        return doc
