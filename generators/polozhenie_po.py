# -*- coding: utf-8 -*-
"""
Генератор «Положение о Проектном офисе по производственной эффективности» (doc_type=polozhenie_po).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — чистый шаблон doc_configs (ООО «НАЗВАНИЕ КОМПАНИИ», без логотипа).
4 метки: организация (УТВЕРЖДАЮ + заголовок + тело п.1.1), подписант УТВЕРЖДАЮ (должность+ФИО),
статус ПО в п.1.1. Тело Положения
(общие положения, задачи, оргструктура, права, ответственность, лист ознакомления, блок «Составлено») — методкаркас.
Город г. Москва (footer). Серая заливка-маркер снята при сборке.
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PolozheniePo:
    """
    Генератор «Положение о Проектном офисе по производственной эффективности». Пользователь вводит
    4 поля (все обязательные, source=own): организация, должность и ФИО утверждающего (гриф
    УТВЕРЖДАЮ) и статус ПО в пункте 1.1 — «является» или «не является» структурным подразделением. Тело Положения (общие положения, задачи, оргструктура, права,
    ответственность, лист ознакомления) и город г. Москва зашиты в шаблон polozhenie_po.docx.
    """
    DOC_TYPE = "polozhenie_po"
    TITLE = "Положение о Проектном офисе по производственной эффективности"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "polozhenie_po.docx")
    SCHEMA = [
        {"key": "org_full",    "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "signer_post", "label": "Должность утверждающего (УТВЕРЖДАЮ)", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО утверждающего (УТВЕРЖДАЮ)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
        # Пункт 1.1: в шаблоне заказчика стояло «(не)является» — теперь выбор эксперта
        # (обратная связь 14.07). Значение подставляется в текст пункта как есть.
        {"key": "po_status",   "label": "Проектный офис (п. 1.1)", "type": "select", "required": True, "source": "own",
         "options": ["является", "не является"], "default": "является",
         "hint": "является / не является структурным подразделением предприятия"},
    ]
    def defaults(self) -> dict:
        """значения по умолчанию из схемы (здесь — статус ПО в пункте 1.1)"""
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
