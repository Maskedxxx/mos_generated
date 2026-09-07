# Как добавить свой тип документа (генератор)

Тип = шаблон Word с метками + класс-генератор + строка в реестре + узел в графе.
Код генератора — 40 строк по образцу, логики в нём нет: схема полей и вызов `docxtpl`.

## 1. Шаблон `templates/<тип>.docx`

Взять чистый образец документа заказчика и заменить переменные части метками Jinja:
`{{org_full}}`, `{{prikaz_num}}`, `{{prikaz_date}}` и т.д. Постоянный текст остаётся в шаблоне.

Проверить, что метка — один текстовый фрагмент (run) в `word/document.xml`: Word при
редактировании часто разрывает `{{org_full}}` на `{{org` + `_full}}` (разное форматирование,
проверка орфографии), и docxtpl её не увидит. Быстрая проверка:

```bash
unzip -p templates/<тип>.docx word/document.xml | grep -o '{{[^}]*}}' | sort -u
```

Все метки должны вывестись целиком. Текст внутри текстбоксов (`w:txbxContent`) docxtpl тоже
обрабатывает, но правки там делать через zip, python-docx их не видит.

## 2. Генератор `generators/<тип>.py`

Скопировать `generators/prikaz_ppu.py` (самый короткий образец) и заменить:

```python
class PrikazExample:
    DOC_TYPE = "prikaz_example"                       # = имя файла шаблона и ключ в реестре
    TITLE = "Приказ об утверждении регламента"        # заголовок в форме
    TEMPLATE = str(Path(__file__).resolve().parent.parent / "templates" / "prikaz_example.docx")

    SCHEMA = [
        {"key": "org_full",    "label": "Организация (юр.форма + наименование)", "type": "text", "required": True, "source": "own", "hint": "ООО «Ромашка»"},
        {"key": "prikaz_num",  "label": "Номер приказа",  "type": "text", "required": True, "source": "own", "hint": "12-ПТ"},
        {"key": "prikaz_date", "label": "Дата приказа",   "type": "text", "required": True, "source": "own", "hint": "«26» мая 2026 г."},
        {"key": "signer_role", "label": "Должность подписанта", "type": "text", "required": True, "source": "own", "default": "Генеральный директор"},
        {"key": "signer_fio",  "label": "ФИО подписанта (И.О. Фамилия)", "type": "text", "required": True, "source": "own"},
    ]
```

Методы `defaults()`, `context()`, `generate()` — как в образце, менять не нужно. Правила схемы:

| Поле | Что |
|---|---|
| `key` | ровно как метка в шаблоне; одинаковые ключи в разных типах (`org_full`, `signer_fio`) дают автозаполнение по организации между типами |
| `required` | проверяется после подстановки дефолтов; незаполненные → `ValueError` → HTTP 400 с перечнем |
| `source` | `own` — вводит пользователь; `inherited` — если пусто, берётся из сессии (то, что вводили в предыдущем документе) |
| `default` | значение по умолчанию (например, реквизиты РЦК); пользователь может изменить |
| `hint` | подсказка-плейсхолдер в форме |

Если под шаблон нужна подготовка значений (склонение, вычисляемые поля) — переопределить
`context()`; образец — генераторы с дополнительными методами в `generators/`.

## 3. Реестр `registry.py`

```python
from generators.prikaz_example import PrikazExample
...
GENERATORS = {
    ...
    PrikazExample.DOC_TYPE: PrikazExample,
}
```

## 4. Граф `graph.json`

Добавить узел — код и порядок задают место в выпадающем списке интерфейса:

```json
{"doc_type": "prikaz_example", "title": "Приказ об утверждении регламента", "position": 16, "code": "4.1"}
```

## 5. Проверить

```bash
.venv/bin/pytest -q tests/test_generators.py -k prikaz_example   # схема, docx без {{ }}, обязательные
.venv/bin/pytest -q tests/test_api.py                             # граф содержит все типы реестра
bash scripts/restart.sh
curl -s http://localhost:8090/api/types/prikaz_example/schema
curl -s -o /tmp/x.docx "http://localhost:8090/api/types/prikaz_example/download?org_full=ООО+Тест&prikaz_num=1&prikaz_date=01.09.2026&signer_fio=Иванов+И.И."
```

Тесты параметризованы реестром — новый тип попадает в них автоматически. Открыть `/tmp/x.docx`
и сверить с образцом заказчика глазами: метки подставились, форматирование не поехало.
