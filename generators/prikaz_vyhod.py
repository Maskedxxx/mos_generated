# -*- coding: utf-8 -*-
"""
Генератор «Приказ об утверждении правил организации и графика выхода на производственную площадку»
(doc_type=prikaz_vyhod). Контракт skill mosgen-dev §1.1. Эталон prikaz_vyhod_ok (ООО «Пример») без логотипа.
9 меток: org, номер, дата, организатор (п.1) и секретарь (п.2) должность+ФИО, подписант. Методкаркас
(заголовок, преамбула, п.3 график, п.4 контроль) зашит. Город г. Москва константой.
ФИО организатора/секретаря — эксперт вводит в вин. падеже.
"""
from pathlib import Path
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazVyhod:
    DOC_TYPE = "prikaz_vyhod"
    TITLE = "Приказ об утверждении правил организации и графика выхода на производственную площадку"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_vyhod.docx")
    SCHEMA = [
        {"key": "org_full",       "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",     "label": "Номер приказа", "type": "text", "required": True, "source": "own", "hint": "07/19"},
        {"key": "prikaz_date",    "label": "Дата приказа", "type": "text", "required": True, "source": "own", "hint": "22 июля 2026"},
        {"key": "organizer_post", "label": "Должность организатора выхода (вин. падеж, п.1)", "type": "text", "required": True, "source": "own", "hint": "начальника производства"},
        {"key": "organizer_fio",  "label": "ФИО организатора выхода (вин. падеж, п.1)", "type": "text", "required": True, "source": "own", "hint": "Иванова Ивана Александровича"},
        {"key": "secretary_post", "label": "Должность секретаря выхода (вин. падеж, п.2)", "type": "text", "required": True, "source": "own", "hint": "бухгалтера"},
        {"key": "secretary_fio",  "label": "ФИО секретаря выхода (вин. падеж, п.2)", "type": "text", "required": True, "source": "own", "hint": "Петрову Ольгу Алексеевну"},
        {"key": "signer_post",    "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",     "label": "ФИО подписанта (Фамилия И.О.)", "type": "text", "required": True, "source": "own", "hint": "Картошкин М.С."},
    ]
    def defaults(self): return {f["key"]: f["default"] for f in self.SCHEMA if "default" in f}
    def context(self, values):
        ctx=self.defaults(); ctx.update({k:v for k,v in (values or {}).items() if v not in (None,"")}); return ctx
    def generate(self, values):
        ctx=self.context(values)
        missing=[f["key"] for f in self.SCHEMA if f.get("required") and not ctx.get(f["key"])]
        if missing: raise ValueError(f"Не заполнены обязательные поля: {missing}")
        if DocxTemplate is None: raise RuntimeError("docxtpl не установлен")
        doc=DocxTemplate(self.TEMPLATE); doc.render(ctx); return doc
