# -*- coding: utf-8 -*-
"""
Генератор «Приказ о создании информационного центра пилотного потока» (doc_type=prikaz_ic_potoka).
Контракт генератора — docs/ADD_GENERATOR.md. Близнец prikaz_ic: те же 7 меток, но методический каркас — потока-версия
(эталон ООО Слон без логотипа): Регламент, форма-картинка, Матрица (Оперативное управление + 5 блоков),
Лист ознакомления зашиты. Город г. Москва в шапке. Плейсхолдеры самодостаточные (source=own).
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazIcPotoka:
    """
    Генератор «Приказ о создании информационного центра пилотного потока» — .docx по шаблону prikaz_ic_potoka.docx.
    Пользователь вводит 7 обязательных полей (все source=own, без дефолтов и наследования): организация, номер и дата
    приказа, дата начала заполнения разделов (п.3), срок ознакомления с Регламентом (п.4), должность и ФИО подписанта.
    В шаблон зашиты: город г. Москва, Регламент, форма-картинка, Матрица (Оперативное управление + 5 блоков), Лист ознакомления.
    """
    DOC_TYPE = "prikaz_ic_potoka"
    TITLE = "Приказ о создании информационного центра пилотного потока"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_ic_potoka.docx")
    SCHEMA = [
        {"key": "org_full",       "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",     "label": "Номер приказа", "type": "text", "required": True, "source": "own", "hint": "6-ПТ"},
        {"key": "prikaz_date",    "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "15 мая 2026 г."},
        {"key": "date_pristupit", "label": "Дата, с которой приступить к заполнению разделов (п.3)", "type": "text", "required": True, "source": "own", "hint": "01.06.2026"},
        {"key": "date_oznak",     "label": "Срок ознакомления с Регламентом (п.4)", "type": "text", "required": True, "source": "own", "hint": "29.05.2026"},
        {"key": "signer_post",    "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",     "label": "ФИО подписанта (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
    ]
    def defaults(self) -> dict:
        """значения по умолчанию из схемы"""
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
