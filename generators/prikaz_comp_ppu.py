# -*- coding: utf-8 -*-
"""
Генератор документа «Приказ о конкурсах проектов и ППУ» (doc_type=prikaz_comp_ppu).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — «ПРИМЕР №2 ООО Содекс» (docx). Структура
приказа о конкурсах идентична приказу о ППУ (методический текст про конкурсы зашит),
переменные — реквизиты и подписант. Плейсхолдеры самодостаточные, город «г. Москва» константа.
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazCompPpu:
    """
    Генератор «Приказ о конкурсах проектов и ППУ». Пользователь вводит 6 полей (все обязательные,
    source=own, inherited нет): организация, номер и дата приказа, ответственный за конкурсы (вин. падеж),
    должность подписанта (default «Генеральный директор») и его ФИО. Методический текст приказа
    о конкурсах и город «г. Москва» зашиты в шаблон prikaz_comp_ppu.docx.
    """
    DOC_TYPE = "prikaz_comp_ppu"
    TITLE = "Приказ о конкурсах проектов и ППУ"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_comp_ppu.docx")
    SCHEMA = [
        {"key": "org_full",    "label": "Организация (юр.форма + наименование)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",  "label": "Номер приказа",                         "type": "text", "required": True, "source": "own", "hint": "13-ПТ"},
        {"key": "prikaz_date", "label": "Дата приказа",                          "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "responsible", "label": "Ответственный за организацию конкурсов ППУ (ФИО, вин. падеж)", "type": "text", "required": True, "source": "own", "hint": "начальника отдела Иванова И.И."},
        {"key": "signer_role", "label": "Должность подписанта",                  "type": "text", "required": True, "source": "own", "default": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО подписанта (И.О. Фамилия)",         "type": "text", "required": True, "source": "own", "hint": "Б.Л. Дубнев"},
    ]

    def defaults(self) -> dict:
        """значения по умолчанию из схемы"""
        return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}

    def context(self, values: dict) -> dict:
        """итоговый контекст: дефолты, поверх — непустые значения эксперта"""
        ctx = self.defaults()
        ctx.update({k: v for k, v in (values or {}).items() if v not in (None, "")})
        return ctx

    def generate(self, values: dict) -> Any:
        """собрать .docx: проверить обязательные → подставить в шаблон. Возвращает DocxTemplate (API сохранит)."""
        ctx = self.context(values)
        missing = [f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None:
            raise RuntimeError("docxtpl не установлен")
        doc = DocxTemplate(self.TEMPLATE)
        doc.render(ctx)
        return doc
