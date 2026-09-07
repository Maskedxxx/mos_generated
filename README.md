# mos_generated — генерация документов по шаблонам

Сервис собирает готовые `.docx` по утверждённым шаблонам: пользователь заполняет форму
(организация, должности, ФИО, даты, номера), сервис подставляет значения в шаблон Word
и отдаёт файл. Языковая модель не используется — генерация детерминированная.
Дуален сервису проверки документов (`mos_analiz`): тот проверяет те же типы, этот их создаёт.

Заведено **15 типов** (приказы, положения, акт, протокол, чек-лист), все — через `docxtpl`.

## Как это работает

```
GET /api/graph                  → список типов с кодами и порядком (graph.json)
GET /api/types/{тип}/schema     → поля формы из SCHEMA генератора
GET /api/types/{тип}/download?<поля>&session_id=…   (или POST …/generate с JSON)
  │
  ├─ engine.generate(): наследование значений из сессии (поля source=inherited)
  ├─ генератор: дефолты ← значения формы → проверка обязательных → docxtpl.render(шаблон)
  ├─ стор по организации: непустые значения запоминаются под нормализованным названием ООО
  └─ журнал: logs_generated/<тип>/session_<время>/ (meta.json, values.json, копия .docx)
GET /api/orgs, GET /api/org/suggest?org=…   → автозаполнение формы по ранее введённому
```

Подробно — `docs/ARCHITECTURE.md`. Как добавить свой тип — `docs/ADD_GENERATOR.md`.

## Требования

Python 3.12. Больше ничего: ни модели, ни LibreOffice. Веб-интерфейс — в репозитории
проверки (`mos_analiz`, раздел «Генерация», ходит сюда через прокси `/gen`); в этом
репозитории есть только простой `static/index.html` для проверки вручную.

## Быстрый старт

```bash
git clone <repo> mos_generated && cd mos_generated
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q                      # 56 тестов, ~3 с
bash scripts/restart.sh                  # uvicorn api:app в screen `mosgen`, порт 8090
curl -s http://localhost:8090/api/graph | head -c 200
```

Открыть `http://localhost:8090/` — форма генерации; выбрать тип, заполнить, скачать.

В Docker сервис поднимается вместе с проверкой: `docker compose up -d --build` из
репозитория `mos_analiz` (этот репозиторий должен лежать рядом — `../mos_generated`).

## Конфигурация

Всё необязательно, задаётся в `.env` (образец `.env.example`):

| Переменная | Что | По умолчанию |
|---|---|---|
| `GEN_HOST`, `GEN_PORT` | адрес и порт uvicorn в `scripts/restart.sh` | `0.0.0.0`, 8090 |
| `GEN_TRACES_DIR` | журнал генераций | `logs_generated/` в корне |
| `GEN_ORG_STORE` | стор значений по организациям (содержит ФИО — в git нет) | `_org_store.json` в корне |
| `LOG_DIR` | лог процесса | `/tmp` |

## Структура репозитория

```
api.py               HTTP-слой FastAPI: graph, schema, generate, download, orgs, org/suggest, session
engine.py            движок: сессии, стор по организациям, журнал трейсов, единая точка generate()
registry.py          реестр генераторов: doc_type → класс (единственное место регистрации)
graph.json           типы с кодами (0.1 … 3.10) и порядком в интерфейсе
generators/<тип>.py  генератор: DOC_TYPE, TITLE, TEMPLATE, SCHEMA, defaults/context/generate
templates/<тип>.docx шаблон Word с метками {{ключ}}
static/index.html    простой фронт для ручной проверки
scripts/             restart.sh, healthcheck.sh
tests/               pytest: генераторы, стор ООО, API
docs/                ARCHITECTURE.md, ADD_GENERATOR.md
logs_generated/      журнал (не в git)
```

## Использование

**Схема поля формы** (`SCHEMA` генератора → `/schema`): `key` (метка `{{key}}` в шаблоне),
`label`, `type`, `required`, `source` (`own` — вводит пользователь; `inherited` — подтягивается
из сессии, если уже вводилось в другом документе), `hint`, `default`.

**Сессия** — строка `session_id` в запросе: значения накапливаются в памяти процесса и
наследуются следующими документами той же сессии (перезапуск сервиса их сбрасывает;
долговременная память — стор по организации).

**Ошибки:** незаполненные обязательные → `400` с перечнем ключей; неизвестный тип → `404`.

**Сколько документов выпущено:** `find logs_generated -maxdepth 2 -type d -name "session_*" | wc -l`.

## После правок

Код — `bash scripts/restart.sh`. Шаблоны и `graph.json` перечитываются на каждый запрос.
Шаблон правится точечно (это рабочие файлы заказчика): бэкап, затем правка `word/document.xml`
внутри zip; метки `{{ключ}}` не должны разрываться форматированием Word на несколько
фрагментов — иначе docxtpl их не увидит.
