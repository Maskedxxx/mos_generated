# -*- coding: utf-8 -*-
"""
Генератор «Приказ о назначении ответственных лиц за реализацию Программы» (doc_type=prikaz_otvetstvennyh).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — ЧИСТЫЙ бланк «наименование предприятия V2» (Динас) без логотипа:
план задач и привязки приложений уже пустые, реальные данные убраны -> скелет. Проза размечена, участники
рабочих групп (Приложение №1) бланкированы (эксперт дозаполняет в готовом доке). Город «г. Москва» и весь
методический текст/образец-карточка зашиты. Ответственные в им. и дат. падеже — отдельные поля (эксперт
пишет падеж сам; LLM в ядре запрещён §4.5).
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazOtvetstvennyh:
    """
    Генератор «Приказ о назначении ответственных лиц» — .docx по шаблону prikaz_otvetstvennyh.docx.
    Пользователь вводит 16 обязательных полей (все source=own, без дефолтов и наследования): организация, номер и дата приказа,
    5 ответственных resp1..resp5, пилотный поток, срок по руководителю проектного офиса, 4 поля в дат. падеже (*_dat), подписант.
    В шаблон зашиты: город «г. Москва», методический текст, образец-карточка, бланки участников рабочих групп (Приложение №1).
    """
    DOC_TYPE = "prikaz_otvetstvennyh"
    TITLE = "Приказ о назначении ответственных лиц"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_otvetstvennyh.docx")
    SCHEMA = [
        {"key": "org_full",     "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",   "label": "Номер приказа",  "type": "text", "required": True, "source": "own", "hint": "БП-1"},
        {"key": "prikaz_date",  "label": "Дата приказа",   "type": "text", "required": True, "source": "own", "hint": "«02» декабря 2025 г."},
        {"key": "resp1", "label": "Ответственный 1 — Руководитель Программы (должность, ФИО, тел., почта)", "type": "text", "required": True, "source": "own", "hint": "начальник производства, Иванов Иван Иванович, 89000000000, ii@romashka.ru"},
        {"key": "resp2", "label": "Ответственный 2 — «Управление производительностью труда» (должность, ФИО, тел., почта)", "type": "text", "required": True, "source": "own", "hint": "финансовый директор, Петров П.П., ..."},
        {"key": "resp3", "label": "Ответственный 3 — «Оптимизация потоков» (должность, ФИО, тел., почта)", "type": "text", "required": True, "source": "own", "hint": "начальник цеха, Сидоров С.С., ..."},
        {"key": "resp4", "label": "Ответственный 4 — «Управление проектами и изменениями» (должность, ФИО, тел., почта)", "type": "text", "required": True, "source": "own", "hint": "директор по персоналу, Кузнецова К.К., ..."},
        {"key": "resp5", "label": "Ответственный 5 — Менеджер по управлению изменениями (должность, ФИО, тел., почта)", "type": "text", "required": True, "source": "own", "hint": "администратор программы, Смирнова С.С., ..."},
        {"key": "pilot_potok",  "label": "Название пилотного потока", "type": "text", "required": True, "source": "own", "hint": "Производство фитингов"},
        {"key": "po_date",      "label": "Срок предложения по руководителю проектного офиса", "type": "text", "required": True, "source": "own", "hint": "23.02.2026"},
        {"key": "resp_upt_dat", "label": "Ответственный по «Управление ПТ» (должность+ФИО, дат. падеж — «кому обеспечить»)", "type": "text", "required": True, "source": "own", "hint": "Финансовому директору Петрову П.П."},
        {"key": "resp_opt_dat", "label": "Ответственный по «Оптимизация потоков» (должность+ФИО, дат. падеж)", "type": "text", "required": True, "source": "own", "hint": "Начальнику цеха Сидорову С.С."},
        {"key": "resp_upi_dat", "label": "Ответственный по «Управление проектами» (должность+ФИО, дат. падеж)", "type": "text", "required": True, "source": "own", "hint": "Директору по персоналу Кузнецовой К.К."},
        {"key": "oznak_dat",    "label": "Кто организует ознакомление (должность+ФИО, дат. падеж)", "type": "text", "required": True, "source": "own", "hint": "Начальнику производства Иванову И.И."},
        {"key": "signer_post",  "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",   "label": "ФИО подписанта (Фамилия И.О.)", "type": "text", "required": True, "source": "own", "hint": "Иванов И.И."},
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
