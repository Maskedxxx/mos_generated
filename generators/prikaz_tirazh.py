# -*- coding: utf-8 -*-
"""
Генератор «Приказ о переходе программы на фазу Тиражирование» (doc_type=prikaz_tirazh).
Контракт skill mosgen-dev §1.1. Эталон — ЧИСТАЯ болванка «наименование предприятия» (без логотипа),
переменные места были размечены жёлтой заливкой. Собран скелет: жёлтые прозаические места -> метки
(заливка снята). Таблицы (цели, планы) и подписи приложений — методический каркас с fill-in бланками
(эксперт дозаполняет). Город «г. Москва» и весь методический текст зашиты. Плейсхолдеры самодостаточные.
"""
from pathlib import Path
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


class PrikazTirazh:
    DOC_TYPE = "prikaz_tirazh"
    TITLE = "Приказ о переходе на этап Тиражирования"
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_tirazh.docx")
    SCHEMA = [
        {"key": "org_full",    "label": "Наименование организации (юр.форма + название)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",  "label": "Номер приказа",  "type": "text", "required": True, "source": "own", "hint": "БП-2"},
        {"key": "prikaz_date", "label": "Дата приказа",   "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "resp1", "label": "Руководитель Программы (должность, ФИО)", "type": "text", "required": True, "source": "own", "hint": "1-ый заместитель ГД, Иванов И.И."},
        {"key": "resp2", "label": "Руководитель направления «Оптимизация потоков» (должность, ФИО)", "type": "text", "required": True, "source": "own", "hint": "руководитель производственной службы, Петров П.П."},
        {"key": "resp3", "label": "Руководитель направления «Управление проектами и изменениями» (должность, ФИО)", "type": "text", "required": True, "source": "own", "hint": "руководитель службы по управлению персоналом, Сидоров С.С."},
        {"key": "oznak_fio",   "label": "ФИО руководителя кадровой службы (кто ознакомит)", "type": "text", "required": True, "source": "own", "hint": "Кузнецова К.К."},
        {"key": "cancel_date", "label": "Дата отменяемого приказа о назначении ответственных", "type": "text", "required": True, "source": "own", "hint": "02.12.2025 г."},
        {"key": "signer_post", "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "hint": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО подписанта (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
        {"key": "app_sig1", "label": "Приложение — подпись «Заместитель директора по производству» (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "П.П. Петров"},
        {"key": "app_sig2", "label": "Приложение — подпись «Руководитель Программы» (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "И.И. Иванов"},
        {"key": "app_sig3", "label": "Приложение — подпись «Заместитель директора по управлению персоналом» (И.О. Фамилия)", "type": "text", "required": True, "source": "own", "hint": "К.К. Кузнецова"},
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
