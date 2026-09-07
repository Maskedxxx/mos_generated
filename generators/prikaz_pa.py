# -*- coding: utf-8 -*-
"""
Генератор «Приказ о ведении производственного анализа» (doc_type=prikaz_pa).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон ФорСИ без логотипа. Скелет: org, номер, дата,
должности+ФИО ответственных (п.1 ведение ПА, п.1.3 адресат отчётности, п.3 управление проектами,
п.4 ознакомление) и подписант → 13 меток. Методический каркас (преамбула, МУ-55-2024 ФЦК, формы
Приложений 1-3, направление «Управление проектами и изменениями») зашит. Город г. Москва.
ФИО ответственных — эксперт вводит в нужном падеже (дательный для поручений, родительный для адресата).
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazPa:
    """
    Генератор «Приказ о ведении производственного анализа» — .docx по шаблону prikaz_pa.docx.
    Пользователь вводит 13 обязательных полей (все source=own, без дефолтов и наследования): организация, номер и дата приказа,
    должность+ФИО ответственных в нужном падеже (ведение ПА п.1, адресат отчётности п.1.3, управление проектами п.3, ознакомление п.4), подписант.
    В шаблон зашиты: город г. Москва, преамбула, МУ-55-2024 ФЦК, формы Приложений 1-3, направление «Управление проектами и изменениями».
    """
    DOC_TYPE = "prikaz_pa"
    TITLE = "Приказ о ведении производственного анализа"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_pa.docx")
    SCHEMA = [
        {"key": "org_full",    "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",  "label": "Номер приказа", "type": "text", "required": True, "source": "own", "hint": "12-ПА"},
        {"key": "prikaz_date", "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "20 мая 2026 г."},
        {"key": "resp1_post",  "label": "Должность ответственного за ведение ПА (дат. падеж, п.1)", "type": "text", "required": True, "source": "own", "hint": "Начальнику производственного отдела"},
        {"key": "resp1_fio",   "label": "ФИО ответственного за ведение ПА (дат. падеж, п.1)", "type": "text", "required": True, "source": "own", "hint": "Иванову Ивану Ивановичу"},
        {"key": "report_post", "label": "Должность адресата ежемесячной отчётности (род. падеж, п.1.3)", "type": "text", "required": True, "source": "own", "hint": "генерального директора"},
        {"key": "report_fio",  "label": "ФИО адресата ежемесячной отчётности (род. падеж, п.1.3)", "type": "text", "required": True, "source": "own", "hint": "Петрова П.П."},
        {"key": "proj_post",   "label": "Должность ответственного за управление проектами (дат. падеж, п.3)", "type": "text", "required": True, "source": "own", "hint": "Специалисту по проектам"},
        {"key": "proj_fio",    "label": "ФИО ответственного за управление проектами (дат. падеж, п.3)", "type": "text", "required": True, "source": "own", "hint": "Сидорову Сидору Сидоровичу"},
        {"key": "oznak_post",  "label": "Должность ответственного за ознакомление (дат. падеж, п.4)", "type": "text", "required": True, "source": "own", "hint": "Начальнику отдела кадров"},
        {"key": "oznak_fio",   "label": "ФИО ответственного за ознакомление (дат. падеж, п.4)", "type": "text", "required": True, "source": "own", "hint": "Кузнецову Кузьме Кузьмичу"},
        {"key": "signer_post", "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО подписанта (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
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
