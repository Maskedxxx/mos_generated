# -*- coding: utf-8 -*-
"""
Генератор документа «Положение о конкурсах проектов и ППУ» (doc_type=polozhenie_comp_ppu).
Контракт skill mosgen-dev §1.1. Эталон — «ПРИМЕР №4 ООО Бизнес-отель» (docx). Тело —
фиксированный методический регламент о конкурсах (разделы, номинации, УТВЕРЖДАЮ),
компанийонезависимо; переменное — привязка к родительскому приказу в шапке T0.
"""
from pathlib import Path
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PolozhenieCompPpu:
    DOC_TYPE = "polozhenie_comp_ppu"
    TITLE = "Положение о конкурсах проектов и ППУ"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "polozhenie_comp_ppu.docx")
    SCHEMA = [
        {"key": "prikaz_date", "label": "Дата приказа (Положение — Приложение №1 к нему)", "type": "text", "required": True, "source": "own", "hint": "01.09.2025 или «26» мая 2026 г."},
        {"key": "prikaz_num",  "label": "Номер приказа",                                   "type": "text", "required": True, "source": "own", "hint": "13-ПТ"},
    ]

    def defaults(self):
        return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}

    def context(self, values):
        ctx = self.defaults()
        ctx.update({k: v for k, v in (values or {}).items() if v not in (None, "")})
        return ctx

    def generate(self, values):
        ctx = self.context(values)
        missing = [f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None:
            raise RuntimeError("docxtpl не установлен")
        doc = DocxTemplate(self.TEMPLATE)
        doc.render(ctx)
        return doc
