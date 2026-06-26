# -*- coding: utf-8 -*-
"""
Генератор документа «Акт начала мероприятий» (doc_type=akt_nachala) — START-узел графа.

Контракт (см. skill mosgen-dev §1.1): DOC_TYPE, TEMPLATE, SCHEMA, generate(values).
Сборка через docxtpl: реальный .docx-шаблон с метками {{...}}, подстановка значений.
"""
from pathlib import Path

try:
    from docxtpl import DocxTemplate
except ImportError:  # docxtpl ставится в venv сервиса (см. §5); до установки модуль импортируется, но не рендерит
    DocxTemplate = None


class AktNachala:
    DOC_TYPE = "akt_nachala"
    TITLE = "Акт начала мероприятий"
    # путь к шаблону относительно корня сервиса: mos_generated/templates/akt_nachala.docx
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "akt_nachala.docx")

    # Описание плейсхолдеров. key = метка {{key}} в шаблоне. source=own (START — всё вводится).
    # РЦК-поля (rck_*, doverennost) идут с дефолтом — преднаполнены, но эксперт может изменить.
    SCHEMA = [
        # --- Предприятие (вводит эксперт) ---
        {"key": "org_full",          "label": "Организация (юр.форма + название)",        "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "org_rep_role_gen",  "label": "Должность подписанта (в «в лице…», род.)",  "type": "text", "required": True, "source": "own", "hint": "генерального директора"},
        {"key": "org_rep_fio_gen",   "label": "ФИО подписанта (в «в лице…», род.)",        "type": "text", "required": True, "source": "own", "hint": "Иванова Ивана Ивановича"},
        {"key": "org_rep_role_nom",  "label": "Должность подписанта (в блоке подписи)",    "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "org_rep_fio_short", "label": "ФИО подписанта кратко (подпись)",           "type": "text", "required": True, "source": "own", "hint": "Иванов И.И."},
        # --- Даты и Соглашение ---
        {"key": "act_date",          "label": "Дата акта (она же — дата начала, п.1)",     "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "agreement_date",    "label": "Дата Соглашения",                           "type": "text", "required": True, "source": "own", "hint": "«15» мая 2026 г."},
        {"key": "agreement_num",     "label": "Номер Соглашения",                          "type": "text", "required": True, "source": "own", "hint": "№36-104-2026/ППТ"},
        # --- РЦК (с дефолтом, можно изменить) ---
        {"key": "rck_rep_role_gen",  "label": "РЦК: должность представителя (род.)",        "type": "text", "required": True, "source": "own", "default": "заместителя начальника управления"},
        {"key": "rck_rep_fio_gen",   "label": "РЦК: ФИО представителя (род.)",             "type": "text", "required": True, "source": "own", "default": "Ахмедьянова Дениса Арэвкатовича"},
        {"key": "rck_rep_role_nom",  "label": "РЦК: должность (подпись)",                  "type": "text", "required": True, "source": "own", "default": "Заместитель начальника управления"},
        {"key": "rck_rep_fio_short", "label": "РЦК: ФИО кратко (подпись)",                 "type": "text", "required": True, "source": "own", "default": "Ахмедьянов Д.А."},
        {"key": "doverennost",       "label": "Доверенность РЦК (дата и номер)",           "type": "text", "required": True, "source": "own", "default": "08.12.2025 №17/2025"},
    ]

    def defaults(self) -> dict:
        """значения по умолчанию из схемы (РЦК-поля)"""
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
