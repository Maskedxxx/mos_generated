# -*- coding: utf-8 -*-
"""
Генератор документа «Приказ о системе подачи и реализации ППУ» (doc_type=prikaz_ppu).

Контракт (см. skill mosgen-dev §1.1): DOC_TYPE, TEMPLATE, SCHEMA, generate(values).
Сборка через docxtpl: шаблон templates/prikaz_ppu.docx с метками {{...}} (эталон —
канонический образец заказчика «ПРИМЕР №1 ООО Содекс»). Плейсхолдеры самодостаточные
(наследование между типами не используется — графа заказчика пока нет).
Город издания «г. Москва» и весь методический текст зашиты в шаблон (константы проекта).
"""
from pathlib import Path

try:
    from docxtpl import DocxTemplate
except ImportError:  # docxtpl ставится в venv сервиса
    DocxTemplate = None


class PrikazPpu:
    DOC_TYPE = "prikaz_ppu"
    TITLE = "Приказ о системе подачи и реализации ППУ"
    # путь к шаблону относительно корня сервиса: mos_generated/templates/prikaz_ppu.docx
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_ppu.docx")

    # Плейсхолдеры (key = метка {{key}} в шаблоне). Все source=own — эксперт вводит.
    SCHEMA = [
        {"key": "org_full",    "label": "Организация (юр.форма + наименование)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",  "label": "Номер приказа",                         "type": "text", "required": True, "source": "own", "hint": "12-ПТ"},
        {"key": "prikaz_date", "label": "Дата приказа",                          "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "responsible", "label": "Ответственный за организацию подачи и сбора ППУ (ФИО, вин. падеж)", "type": "text", "required": True, "source": "own", "hint": "Иванову И.И. / начальника отдела Иванова И.И."},
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

    def generate(self, values: dict):
        """собрать .docx: проверить обязательные → подставить в шаблон. Возвращает DocxTemplate (API сохранит)."""
        ctx = self.context(values)
        # проверка обязательных полей (после мёржа дефолтов)
        missing = [f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None:
            raise RuntimeError("docxtpl не установлен (нужен в venv сервиса)")
        doc = DocxTemplate(self.TEMPLATE)
        doc.render(ctx)  # подстановка {{...}}
        return doc
