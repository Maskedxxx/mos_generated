# -*- coding: utf-8 -*-
"""
Генератор «Положение о Проектном офисе по производственной эффективности» (doc_type=polozhenie_po).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — чистый шаблон doc_configs (ООО «НАЗВАНИЕ КОМПАНИИ», без логотипа).
3 метки: организация (УТВЕРЖДАЮ + заголовок + тело п.1.1), подписант УТВЕРЖДАЮ (должность+ФИО). Тело Положения
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
    3 поля (все обязательные, source=own, дефолтов и inherited нет): организация, должность и ФИО
    утверждающего (гриф УТВЕРЖДАЮ). Тело Положения (общие положения, задачи, оргструктура, права,
    ответственность, лист ознакомления) и город г. Москва зашиты в шаблон polozhenie_po.docx.
    """
    DOC_TYPE = "polozhenie_po"
    TITLE = "Положение о Проектном офисе по производственной эффективности"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "polozhenie_po.docx")
    SCHEMA = [
        {"key": "org_full",    "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "signer_post", "label": "Должность утверждающего (УТВЕРЖДАЮ)", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО утверждающего (УТВЕРЖДАЮ)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
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
