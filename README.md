# 🧠 Daylog AI

> **Умный Telegram-бот для личного дневника на базе ИИ**
> Пишешь как думаешь — бот структурирует, анализирует и возвращает тебе картину твоей жизни.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-009EFF?style=flat-square)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-FSM%20%2F%20Cache-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Sentry](https://img.shields.io/badge/Sentry-monitoring-362D59?style=flat-square&logo=sentry&logoColor=white)](https://sentry.io)

---

## О проекте

**Daylog AI** — это Telegram-бот, который превращает ежедневный поток мыслей в структурированный личный дневник.
Пользователь пишет о своём дне в свободной форме. ИИ задаёт уточняющие вопросы в духе коучинга, извлекает метрики из текста (настроение, продуктивность, энергия, стресс) и в конце недели присылает структурированный дайджест с паттернами и инсайтами.

**Цель** — минимум усилий от пользователя, максимум рефлексии. Никаких форм и трекеров. Просто разговор.

---

## ✨ Ключевые возможности

| Функция | Описание |
|---|---|
| **FSM-диалог** | Многошаговый диалог записи дня с поддержкой до 2 раундов уточняющих вопросов от ИИ |
| **AI-коучинг** | Контекстные вопросы на основе текста пользователя, направленные на углублённую рефлексию |
| **Парсинг метрик** | Автоматическое извлечение оценок настроения, энергии, стресса и продуктивности из свободного текста |
| **Еженедельный дайджест** | Структурированный AI-анализ недели: паттерны, тренды, повторяющиеся темы |
| **Push-напоминания** | Ежедневные вечерние нотификации через `apscheduler` |
| **Каскадный фоллбэк** | Автоматическое переключение между AI-провайдерами при недоступности одного из них |
| **Защита от Prompt Injection** | Санитизация пользовательского ввода на уровне системного промпта |
| **Мониторинг** | Sentry для трассировки async-ошибок, Langfuse для LLM-аналитики |

---

## 🛠 Технический стек

### Ядро
| Компонент | Технология |
|---|---|
| Язык | Python 3.11+ |
| Фреймворк бота | aiogram 3.x |
| FSM / Кеш | Redis (через `RedisStorage`) |
| ORM | SQLAlchemy (async) + asyncpg |
| База данных | PostgreSQL |
| Миграции | Alembic |
| Валидация конфига | pydantic-settings (`.env`) |

### ИИ и аналитика
| Компонент | Технология |
|---|---|
| LLM-провайдер #1 | **Groq** (LLaMA-3) — основной, приоритетный |
| LLM-провайдер #2 | **Google Gemini** (Flash-Lite) — фоллбэк |
| HTTP-клиент | `aiohttp` — прямые запросы к API провайдеров |
| LLM-трассировка | **Langfuse** — аналитика промптов и латентности |

### Инфраструктура
| Компонент | Технология |
|---|---|
| Фоновые задачи | `apscheduler` — напоминания, дайджесты |
| Логирование | `loguru` |
| Мониторинг ошибок | **Sentry** — отлов необработанных async-исключений |
| Контейнеризация | Docker + docker-compose |

---

## 🏗 Архитектура проекта

```
daylog-ai/
│
├── alembic/                    # Миграции базы данных
│   └── versions/               # История ревизий схемы
│
├── assets/                     # Статические файлы (онбординг-изображения)
│
├── bot/                        # Основной пакет бота
│   ├── handlers/               # Роутеры событий aiogram
│   │   ├── start.py            # /start, онбординг, регистрация пользователя
│   │   ├── diary.py            # FSM-диалог: запись дня + AI-коучинг
│   │   ├── history.py          # Просмотр последних записей
│   │   ├── stats.py            # Личная статистика (streak, метрики)
│   │   ├── info.py             # /help, информационные команды
│   │   ├── common.py           # Общие хендлеры (отмена, fallback)
│   │   └── states.py           # FSM-состояния (DiaryStates)
│   │
│   ├── keyboards/
│   │   └── main_kb.py          # Основные inline и reply-клавиатуры
│   │
│   ├── lexicon/                # Тексты сообщений (централизованный i18n-готовый слой)
│   │
│   ├── middlewares/
│   │   ├── throttle.py         # ThrottleMiddleware — защита от флуда
│   │   └── db.py               # DbSessionMiddleware — инжект async-сессии в хендлеры
│   │
│   ├── services/               # Бизнес-логика (без зависимости от Telegram)
│   │   ├── ai.py               # Каскадные LLM-запросы: Groq → Gemini fallback
│   │   ├── prompts.py          # Все системные промпты (централизованно)
│   │   ├── scheduler.py        # Планировщик: напоминания, еженедельные дайджесты
│   │   ├── saver.py            # Логика сохранения записи + парсинг метрик
│   │   └── analytics.py        # Агрегация статистики пользователя
│   │
│   ├── utils/
│   │   └── telegram.py         # Хелперы для работы с Telegram API
│   │
│   └── logging_config.py       # Настройка loguru + Sentry integration
│
├── db/
│   ├── database.py             # Создание async engine и sessionmaker
│   ├── models.py               # SQLAlchemy-модели: User, DiaryEntry
│   └── queries.py              # Все CRUD-операции (без raw SQL)
│
├── config.py                   # Pydantic-settings: загрузка и валидация .env
├── main.py                     # Точка входа: регистрация роутеров, middlewares, polling
│
├── Dockerfile                  # Production-образ бота
├── docker-compose.yml          # Production: bot + postgres + redis
├── docker-compose-dev.yml      # Dev: только инфраструктура (postgres + redis)
├── alembic.ini                 # Конфигурация Alembic
├── requirements.txt
└── .env.example                # Шаблон переменных окружения
```

### Потоки данных

```
Пользователь
    │
    ▼ Telegram Update
[aiogram Dispatcher]
    │
    ├─ [ThrottleMiddleware]      ← Защита от флуда (Redis)
    ├─ [DbSessionMiddleware]     ← Инжект async-сессии из пула
    │
    ▼
[Handler: diary.py / FSM]
    │
    ├─ services/ai.py           ← Запрос к Groq (LLaMA-3)
    │       └─ fallback ──────► Google Gemini Flash-Lite
    │
    ├─ services/saver.py        ← Парсинг метрик + запись в PostgreSQL
    │
    └─ Ответ пользователю
    
[apscheduler]
    ├─ ежедневно  → push-напоминания всем активным пользователям
    └─ еженедельно → AI-дайджест на основе записей за неделю
```

---

## ⚙️ Запуск

### Требования
- Docker & Docker Compose v2+
- Заполненный файл `.env` (см. `.env.example`)

### 1. Клонировать и настроить окружение

```bash
git clone https://github.com/your-repo/daylog-ai.git
cd daylog-ai
cp .env.example .env
# Заполнить .env: токены Telegram, Groq, Gemini, Sentry, Langfuse, пароли DB и Redis
```

### 2. Применить миграции БД

```bash
# Запустить только инфраструктуру
docker compose -f docker-compose-dev.yml up -d

# Применить миграции
docker compose run --rm bot alembic upgrade head
```

### 3. Запустить в продакшне

```bash
docker compose up -d --build
```

### Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot Token от @BotFather |
| `GROQ_API_KEY` | ✅ | API-ключ Groq (основной LLM-провайдер) |
| `GEMINI_API_KEY` | ✅ | API-ключ Google Gemini (фоллбэк) |
| `DATABASE_URL` | ✅ | asyncpg connection string к PostgreSQL |
| `REDIS_URL` | ✅ | Redis connection string (FSM + throttle) |
| `SENTRY_DSN` | ⚪ | DSN для отправки ошибок в Sentry |
| `LANGFUSE_PUBLIC_KEY` | ⚪ | Публичный ключ Langfuse для LLM-трассировки |
| `LANGFUSE_SECRET_KEY` | ⚪ | Секретный ключ Langfuse |
| `DB_ECHO` | ⚪ | Логировать SQL-запросы (`False` по умолчанию) |
| `LOG_LEVEL` | ⚪ | Уровень логирования (`INFO` по умолчанию) |

---

## 🗺 Вектор развития

### 🔄 В работе

- **Telegram Mini App** — пользовательский дашборд: профиль, аналитика метрик, графики настроения/продуктивности
- **Инфраструктура аналитики** — Metabase для product BI + расширение Langfuse-трассировки
- **Оптимизация хранилища** — разделение `conversation_log` и `user_text` в `DiaryEntry` для точного парсинга метрик

### 📋 Бэклог

**Backend & API**
- FastAPI-бэкенд как API-слой для Mini App
- Бесшовная авторизация Telegram Web App (без пароля)
- Индексация PostgreSQL под запросы Mini App

**Frontend**
- React-фронтенд с data fetching из FastAPI
- Дашборд с временными рядами метрик

**ИИ и обработка**
- Поддержка голосовых сообщений (Whisper / STT → дневник)
- Умный роутинг LLM-запросов через LiteLLM
- Контекст предыдущих записей в промптах (персонализация)

**Инфраструктура и безопасность**
- Перевод сервера на SSH-ключи (отказ от парольной аутентификации)
- Principle of Least Privilege для DB-пользователей

**Продукт**
- Английская локализация (i18n)
- Экспорт данных пользователя (GDPR-совместимость)
- Бот-парсер крипто-донатов (real-time tracker)

---

## 📄 Лицензия

Проект разрабатывается в закрытом приватном репозитории. Все права защищены.
