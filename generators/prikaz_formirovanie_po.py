# -*- coding: utf-8 -*-
"""
Генератор «Приказ о формировании Проектного офиса» (doc_type=prikaz_formirovanie_po).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — чистый шаблон doc_configs (ООО «Название»), без логотипа.
23 метки: реквизиты (дата, номер, организация); сроки и ответственные в пунктах (rule 6 — заполнены);
руководитель ПО; 3 специалиста ПО ФИО+должность (rule 7 ≥3 реальных); подписант (должность+ФИО, М.П.).
Тело приказа (пункты-поручения, заголовок) — методкаркас. Город г. Москва константой. Заливка снята.
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazFormirovaniePo:
    """
    Генератор «Приказ о формировании Проектного офиса». Пользователь вводит 23 поля (все обязательные,
    source=own, дефолтов и inherited нет): организация, номер и дата приказа, сроки и ответственные
    по пунктам 1–6 и 8, руководитель ПО, три специалиста ПО (ФИО+должность), подписант.
    Тело приказа (пункты-поручения, заголовок) и город г. Москва зашиты в шаблон prikaz_formirovanie_po.docx.
    """
    DOC_TYPE = "prikaz_formirovanie_po"
    TITLE = "Приказ о формировании Проектного офиса"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_formirovanie_po.docx")
    SCHEMA = [
        {"key": "org_full",       "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",     "label": "Номер приказа", "type": "text", "required": True, "source": "own", "hint": "7-ПО"},
        {"key": "prikaz_date",    "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "20 мая 2026 г."},
        {"key": "srok_sozdat",    "label": "Срок создания ПО (п.1)", "type": "text", "required": True, "source": "own", "hint": "01.06.2026"},
        {"key": "resp2",          "label": "Ответственный за положение о ПО — должность и ФИО (п.2)", "type": "text", "required": True, "source": "own", "hint": "Начальник ОК Иванов И.И."},
        {"key": "srok2",          "label": "Срок (п.2)", "type": "text", "required": True, "source": "own", "hint": "05.06.2026"},
        {"key": "resp3",          "label": "Ответственный за штатное расписание и ДИ — должность и ФИО (п.3)", "type": "text", "required": True, "source": "own", "hint": "Гл. бухгалтер Петров П.П."},
        {"key": "srok3",          "label": "Срок (п.3)", "type": "text", "required": True, "source": "own", "hint": "06.06.2026"},
        {"key": "resp4",          "label": "Ответственный за изменения в штатном расписании — должность и ФИО (п.4)", "type": "text", "required": True, "source": "own", "hint": "Начальник ОК Иванов И.И."},
        {"key": "srok4",          "label": "Срок (п.4)", "type": "text", "required": True, "source": "own", "hint": "07.06.2026"},
        {"key": "resp5",          "label": "Ответственный за рабочие места специалистов — должность и ФИО (п.5)", "type": "text", "required": True, "source": "own", "hint": "Завхоз Сидоров С.С."},
        {"key": "srok5",          "label": "Срок (п.5)", "type": "text", "required": True, "source": "own", "hint": "08.06.2026"},
        {"key": "ruk_po",         "label": "Руководитель ПО — должность и ФИО (п.6)", "type": "text", "required": True, "source": "own", "hint": "Кузнецова К.К."},
        {"key": "srok6",          "label": "Срок назначения руководителя (п.6)", "type": "text", "required": True, "source": "own", "hint": "02.06.2026"},
        {"key": "spec1_fio",      "label": "Специалист ПО №1 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Смирнов А.А."},
        {"key": "spec1_post",     "label": "Специалист ПО №1 — должность", "type": "text", "required": True, "source": "own", "hint": "Руководитель проектов"},
        {"key": "spec2_fio",      "label": "Специалист ПО №2 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Волков В.В."},
        {"key": "spec2_post",     "label": "Специалист ПО №2 — должность", "type": "text", "required": True, "source": "own", "hint": "Специалист по БП"},
        {"key": "spec3_fio",      "label": "Специалист ПО №3 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Зайцева З.З."},
        {"key": "spec3_post",     "label": "Специалист ПО №3 — должность", "type": "text", "required": True, "source": "own", "hint": "Аналитик"},
        {"key": "srok_strategiya","label": "Срок вынесения стратегии на утверждение (п.8)", "type": "text", "required": True, "source": "own", "hint": "30.06.2026"},
        {"key": "signer_post",    "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",     "label": "ФИО подписанта (Фамилия И.О.)", "type": "text", "required": True, "source": "own", "hint": "А.А. Директоров"},
    ]
    def defaults(self) -> dict:
        """значения по умолчанию из схемы (в этой схеме дефолтов нет — пустой словарь)"""
        return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}
    def context(self, values: dict) -> dict:
        """итоговый контекст: дефолты, поверх — непустые значения эксперта"""
        ctx=self.defaults(); ctx.update({k:v for k,v in (values or {}).items() if v not in (None,"")}); return ctx
    def generate(self, values: dict) -> Any:
        """собрать .docx: проверить обязательные → подставить в шаблон. Возвращает DocxTemplate (API сохранит)."""
        ctx=self.context(values)
        missing=[f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing: raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None: raise RuntimeError("docxtpl не установлен")
        doc=DocxTemplate(self.TEMPLATE); doc.render(ctx); return doc
