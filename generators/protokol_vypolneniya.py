# -*- coding: utf-8 -*-
"""
Генератор «Протокол выполнения мероприятий» (doc_type=protokol_vypolneniya).
Контракт skill mosgen-dev §1.1. Эталон — болванка «наименование предприятия МИР ИТ» (логотип —
методический РЦК «Агентство стратегического развития», часть бланка, остаётся). Собран скелет:
данные предприятия убраны в метки, показатели-таблицы бланкированы (эксперт дозаполняет).
ВАЖНО (rule 8): дата протокола = дата конца периода реализации — одна метка {{protokol_date}}.
Город «г. Москва» и методический текст/чек-лист мероприятий зашиты. Плейсхолдеры самодостаточные.
"""
from pathlib import Path
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class ProtokolVypolneniya:
    DOC_TYPE = "protokol_vypolneniya"
    TITLE = "Протокол выполнения мероприятий"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "protokol_vypolneniya.docx")
    SCHEMA = [
        {"key": "org_full",         "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "soglashenie_num",  "label": "Номер Соглашения (в заголовке протокола)", "type": "text", "required": True, "source": "own", "hint": "55-220-2025/ППТ"},
        {"key": "soglashenie_date", "label": "Дата Соглашения о сотрудничестве", "type": "text", "required": True, "source": "own", "hint": "«28» ноября 2025 г."},
        {"key": "period_start",     "label": "Дата начала периода реализации", "type": "text", "required": True, "source": "own", "hint": "«03» декабря 2025 г."},
        {"key": "protokol_date",    "label": "Дата протокола (= дата конца периода реализации)", "type": "text", "required": True, "source": "own", "hint": "«05» июня 2026 г."},
        {"key": "signer_pred_fio",  "label": "ФИО подписанта от Предприятия", "type": "text", "required": True, "source": "own", "hint": "Иванов И.И."},
        {"key": "rck_signer_fio",   "label": "ФИО подписанта от РЦК", "type": "text", "required": True, "source": "own", "default": "Ахмедьянов Д.А."},
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
