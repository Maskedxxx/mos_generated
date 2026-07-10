# -*- coding: utf-8 -*-
"""
Генератор «Чек-лист выбора эталонного участка» (doc_type=cheklist_eu).
Контракт skill mosgen-dev §1.1. Эталон — болванка ООО «Предприятие» (логотип РЦК методический в header).
7 меток: организация, название участка, дата + подписи двух сторон (От предприятия / От УРЦК): должность+ФИО.
Таблица критериев со шкалой 0/1/2 и итог — методкаркас; колонка «Оценка (значение)» и итог пустые (форма).
"""
from pathlib import Path
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class CheklistEu:
    DOC_TYPE = "cheklist_eu"
    TITLE = "Чек-лист выбора эталонного участка"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "cheklist_eu.docx")
    SCHEMA = [
        {"key": "org_full",      "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "uchastok_name", "label": "Название эталонного участка", "type": "text", "required": True, "source": "own", "hint": "Участок сборки системы САР СМ"},
        {"key": "prikaz_date",   "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "22.08.2026"},
        {"key": "signer1_post",  "label": "Должность подписанта от предприятия", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer1_fio",   "label": "ФИО подписанта от предприятия", "type": "text", "required": True, "source": "own", "hint": "А.В. Петров"},
        {"key": "signer2_post",  "label": "Должность подписанта от УРЦК", "type": "text", "required": True, "source": "own", "hint": "Начальник"},
        {"key": "signer2_fio",   "label": "ФИО подписанта от УРЦК", "type": "text", "required": True, "source": "own", "hint": "А.В. Иванов"},
    ]
    def defaults(self): return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}
    def context(self, values):
        ctx=self.defaults(); ctx.update({k:v for k,v in (values or {}).items() if v not in (None,"")}); return ctx
    def generate(self, values):
        ctx=self.context(values)
        missing=[f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing: raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None: raise RuntimeError("docxtpl не установлен")
        doc=DocxTemplate(self.TEMPLATE); doc.render(ctx); return doc
