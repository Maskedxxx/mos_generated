# -*- coding: utf-8 -*-
"""
Генератор «Приказ о формировании Проектного офиса» (doc_type=prikaz_formirovanie_po).
Контракт генератора — docs/ADD_GENERATOR.md. Эталон — чистый шаблон doc_configs (ООО «Название»), без логотипа.
23 метки: реквизиты (дата, номер, организация); сроки и ответственные в пунктах (rule 6 — заполнены);
руководитель ПО; 3 специалиста ПО ФИО+должность (rule 7 ≥3 реальных); подписант (должность+ФИО, М.П.).
Тело приказа (пункты-поручения, заголовок) — методкаркас. Город г. Москва константой. Заливка снята.
Статус ПО (решение владельца 29.09): поле po_status «является / не является» (тот же ключ, что в Положении о ПО).
При «не является» п.3 (штатное расписание и ДИ ПО) и п.4 (изменение штатного расписания и оргструктуры) не требуются:
их поля неактивны (атрибут схемы required_if), а сами пункты из приказа удаляются — блок {%p if po_status == 'является' %}
в шаблоне; нумерация пунктов автоматическая (Word), следующие пункты сдвигаются. Так оформлены приказы в образцах
заказчика (19.10.2026, по просьбе Александра; до этого с 29.09 пункты оставались с прочерком).
"""
from pathlib import Path
from typing import Any
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazFormirovaniePo:
    """
    Генератор «Приказ о формировании Проектного офиса». Пользователь вводит 24 поля (source=own, inherited нет):
    организация, номер и дата приказа, статус ПО (select, по умолчанию «является»), сроки и ответственные
    по пунктам 1–6 и 8, руководитель ПО, три специалиста ПО (ФИО+должность), подписант. Поля п.3 и п.4
    обязательны только при статусе «является» (required_if), иначе пункты 3 и 4 в документ не входят.
    Тело приказа (пункты-поручения, заголовок) и город г. Москва зашиты в шаблон prikaz_formirovanie_po.docx.
    """
    DOC_TYPE = "prikaz_formirovanie_po"
    TITLE = "Приказ о формировании Проектного офиса"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_formirovanie_po.docx")
    # Номера пунктов в подписях — только у п.1–4: при «не является» п.3–4 удаляются и п.5–8 сдвигаются
    SCHEMA = [
        {"key": "org_full",       "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",     "label": "Номер приказа", "type": "text", "required": True, "source": "own", "hint": "7-ПО"},
        {"key": "prikaz_date",    "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "20 мая 2026 г."},
        {"key": "srok_sozdat",    "label": "Срок создания ПО (п.1)", "type": "text", "required": True, "source": "own", "hint": "01.06.2026"},
        {"key": "resp2",          "label": "Ответственный за положение о ПО — должность и ФИО (п.2)", "type": "text", "required": True, "source": "own", "hint": "Начальник ОК Иванов И.И."},
        {"key": "srok2",          "label": "Срок (п.2)", "type": "text", "required": True, "source": "own", "hint": "05.06.2026"},
        # Статус ПО: от него зависят п.3 и п.4 (штатное расписание и оргструктура — только у структурного подразделения)
        {"key": "po_status",      "label": "Проектный офис — структурное подразделение предприятия? (как в п. 1.1 Положения о ПО)", "type": "select", "required": True, "source": "own",
         "options": ["является", "не является"], "default": "является"},
        {"key": "resp3",          "label": "Ответственный за штатное расписание и ДИ — должность и ФИО (п.3)", "type": "text", "required": True, "source": "own", "hint": "Гл. бухгалтер Петров П.П.", "required_if": {"po_status": "является"}},
        {"key": "srok3",          "label": "Срок (п.3)", "type": "text", "required": True, "source": "own", "hint": "06.06.2026", "required_if": {"po_status": "является"}},
        {"key": "resp4",          "label": "Ответственный за изменения в штатном расписании — должность и ФИО (п.4)", "type": "text", "required": True, "source": "own", "hint": "Начальник ОК Иванов И.И.", "required_if": {"po_status": "является"}},
        {"key": "srok4",          "label": "Срок (п.4)", "type": "text", "required": True, "source": "own", "hint": "07.06.2026", "required_if": {"po_status": "является"}},
        {"key": "resp5",          "label": "Ответственный за рабочие места специалистов ПО — должность и ФИО", "type": "text", "required": True, "source": "own", "hint": "Завхоз Сидоров С.С."},
        {"key": "srok5",          "label": "Срок — рабочие места специалистов ПО", "type": "text", "required": True, "source": "own", "hint": "08.06.2026"},
        {"key": "ruk_po",         "label": "Руководитель ПО — должность и ФИО", "type": "text", "required": True, "source": "own", "hint": "Кузнецова К.К."},
        {"key": "srok6",          "label": "Срок назначения руководителя ПО", "type": "text", "required": True, "source": "own", "hint": "02.06.2026"},
        {"key": "spec1_fio",      "label": "Специалист ПО №1 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Смирнов А.А."},
        {"key": "spec1_post",     "label": "Специалист ПО №1 — должность", "type": "text", "required": True, "source": "own", "hint": "Руководитель проектов"},
        {"key": "spec2_fio",      "label": "Специалист ПО №2 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Волков В.В."},
        {"key": "spec2_post",     "label": "Специалист ПО №2 — должность", "type": "text", "required": True, "source": "own", "hint": "Специалист по БП"},
        {"key": "spec3_fio",      "label": "Специалист ПО №3 — ФИО", "type": "text", "required": True, "source": "own", "hint": "Зайцева З.З."},
        {"key": "spec3_post",     "label": "Специалист ПО №3 — должность", "type": "text", "required": True, "source": "own", "hint": "Аналитик"},
        {"key": "srok_strategiya","label": "Срок вынесения стратегии на утверждение", "type": "text", "required": True, "source": "own", "hint": "30.06.2026"},
        {"key": "signer_post",    "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",     "label": "ФИО подписанта (Фамилия И.О.)", "type": "text", "required": True, "source": "own", "hint": "А.А. Директоров"},
    ]
    def defaults(self) -> dict:
        """значения по умолчанию из схемы (статус ПО — «является»)"""
        return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}
    def context(self, values: dict) -> dict:
        """итоговый контекст: дефолты, поверх — непустые значения эксперта"""
        ctx=self.defaults(); ctx.update({k:v for k,v in (values or {}).items() if v not in (None,"")}); return ctx
    def generate(self, values: dict) -> Any:
        """собрать .docx: проверить обязательные → подставить в шаблон. Возвращает DocxTemplate (API сохранит)."""
        ctx=self.context(values)
        # неактивные поля (условие required_if не выполнено): значение формы игнорируется — их пункты (п.3, п.4)
        # шаблон при «не является» не выводит
        inactive=[f["key"] for f in self.SCHEMA if not self.is_active(f, ctx)]
        for k in inactive: ctx.pop(k, None)
        missing=[f["key"] for f in self.SCHEMA if f.get("required") and f["key"] not in inactive and not ctx.get(f["key"])]
        if missing: raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None: raise RuntimeError("docxtpl не установлен")
        doc=DocxTemplate(self.TEMPLATE); doc.render(ctx); return doc
    @staticmethod
    def is_active(field: dict, ctx: dict) -> bool:
        """поле активно, если у него нет required_if или все условия {ключ: значение} выполнены в контексте"""
        return all(ctx.get(k) == v for k, v in (field.get("required_if") or {}).items())
