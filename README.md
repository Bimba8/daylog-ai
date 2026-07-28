# 🧠 DayLog AI

> **Умный Telegram-бот и Mini App для личного дневника на базе ИИ**
> Пишешь как думаешь — бот структурирует, анализирует и возвращает тебе картину твоей жизни через наглядные графики и инсайты.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Mini%20App-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-009EFF?style=flat-square)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-FSM%20%2F%20Cache-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Sentry](https://img.shields.io/badge/Sentry-monitoring-362D59?style=flat-square&logo=sentry&logoColor=white)](https://sentry.io)

---

## 📖 О проекте

**DayLog AI** — это экосистема из Telegram-бота и полноценного Telegram Mini App, которая превращает ежедневный поток мыслей в структурированный личный дневник и аналитику жизни.

Вам не нужно заполнять трекеры или отвечать на скучные формы. Вы просто рассказываете боту о своём дне в свободной форме. ИИ задаёт уточняющие коучинговые вопросы, автоматически извлекает скрытые метрики (настроение, продуктивность, энергию, стресс) и строит наглядный дашборд. В конце недели вы получаете AI-дайджест с паттернами вашего поведения и инсайтами.

---

## ✨ Ключевые возможности

| Функция | Описание |
|---|---|
| **Telegram Mini App** | Полноценный React-фронтенд прямо внутри Telegram. Дашборд с метриками, календарь активности (heatmap) и просмотр истории записей. |
| **FSM-диалог** | Многошаговый диалог записи дня с поддержкой до 2 раундов уточняющих вопросов от ИИ. |
| **AI-коучинг** | Контекстные вопросы на основе текста пользователя, направленные на углублённую рефлексию. |
| **Парсинг метрик** | Автоматическое извлечение оценок (1-5) для настроения, энергии, стресса и продуктивности из свободного текста. |
| **Бесшовная авторизация** | Безопасная JWT-авторизация в Mini App на основе валидации `initData` Telegram. Никаких паролей. |
| **Еженедельный дайджест** | Структурированный AI-анализ недели: паттерны, тренды, повторяющиеся темы. |
| **Каскадный фоллбэк** | Автоматическое переключение между AI-провайдерами (Groq → Gemini) при недоступности одного из них. |
| **Безопасность (AppSec)** | Глубоко проаудированный код. Строгий Rate Limiting (Redis), защита от Prompt Injection во всех AI-ручках, CSP-заголовки, in-memory JWT, валидация полей через Pydantic. |
| **i18n (Локализация)** | Поддержка русского (`ru`) и английского (`en`) языков. Контекстные таймзоны UTC для разных регионов. |

---

## 🛠 Технический стек

### Бэкенд и Бот (Python 3.11+)
* **Фреймворки:** `aiogram 3.x` (Telegram Bot API), `FastAPI` (REST API для Mini App)
* **База данных:** PostgreSQL + `asyncpg` + `SQLAlchemy` (async ORM)
* **Миграции:** Alembic
* **Кэш и Rate Limit:** Redis
* **Фоновые задачи:** `apscheduler` (пуши, дайджесты)
* **Валидация конфигурации:** `pydantic-settings`

### Фронтенд (Telegram Mini App)
* **Core:** React 19, TypeScript, Vite
* **UI/Стилизация:** Tailwind CSS v4, Lucide React (иконки), framer-motion (анимации)
* **API Client:** Нативный fetch с перехватом 401 и строгим in-memory хранением токенов.

### ИИ и аналитика
* **LLM #1 (Primary):** Groq (LLaMA-3)
* **LLM #2 (Fallback):** Google Gemini (Flash)
* **Трассировка:** Langfuse (аналитика промптов, latency, costs)
* **BI:** Metabase (внутренний дашборд для продуктовой аналитики)

### Инфраструктура и Мониторинг
* **Логирование:** `loguru`
* **Сбор ошибок:** Sentry (асинхронный отлов с семплированием `0.1` в проде)
* **Контейнеризация:** Docker + `docker-compose`

---

## 🏗 Архитектура проекта

```text
daylog-ai/
├── api/                        # FastAPI бэкенд
│   ├── routers/                # Эндпоинты (auth, profile, stats)
│   ├── app.py                  # Конфигурация FastAPI и middlewares
│   └── security.py             # Валидация initData Telegram и выдача JWT
│
├── bot/                        # Telegram-бот (aiogram)
│   ├── handlers/               # Роутеры (start, diary, stats, common)
│   ├── middlewares/            # Redis Throttle, DB session, i18n
│   └── services/               # Бизнес-логика: AI, планировщик (scheduler), saver
│
├── frontend/                   # Telegram Mini App (React + Vite)
│   ├── src/
│   │   ├── api/                # API-клиент с In-Memory JWT
│   │   ├── components/         # UI-компоненты (Header, EmptyState)
│   │   ├── screens/            # Экраны (Profile, Calendar, Analytics)
│   │   └── i18n/               # Локализация фронтенда
│
├── db/                         # Работа с базой данных
│   ├── database.py             # Async engine & session
│   ├── models.py               # SQLAlchemy модели (User, DiaryEntry)
│   └── queries.py              # CRUD операции
│
├── config.py                   # Pydantic настройки (загрузка из .env)
├── main.py                     # Точка входа бота (polling + scheduler)
├── Dockerfile                  # Production-образ Python (bot + api)
└── docker-compose.yml          # Оркестрация: app, postgres, redis, metabase, dozzle
```

### 🔒 Архитектура безопасности (AppSec)
DayLog AI построен с фокусом на безопасность пользовательских данных (особенно личных дневников):
1. **API:** CORS строго привязан к домену WebApp. JWT выдается только после криптографической проверки `initData` от серверов Telegram и проверки наличия юзера в БД (защита от ghost-сессий).
2. **Frontend:** Полный отказ от `localStorage` для хранения токенов. Токены хранятся исключительно in-memory, что нивелирует риски кражи сессии при XSS. Строгий `Content-Security-Policy`.
3. **Database:** Защита от N+1 и OOM через отказ от `lazy="selectin"` в пользу точечных загрузок. Raw SQL отсутствует.
4. **LLM:** Защита от Prompt Injection во всех AI-функциях (`generate_insights`, `get_metrics` и др.) с помощью системных разделителей `### USER INPUT ###` и пре-инструкций.

---

## ⚙️ Развертывание

### Требования
- Docker & Docker Compose v2+
- Заполненный файл `.env` (см. `.env.example`)

### 1. Подготовка
```bash
git clone https://github.com/your-repo/daylog-ai.git
cd daylog-ai
cp .env.example .env
# Обязательно заполните: токены Telegram, Groq, Gemini, Sentry, Langfuse, пароли DB/Redis/Metabase, а также JWT_SECRET.
```

### 2. Запуск инфраструктуры разработки
```bash
# Поднимает БД и Redis (привязка к 127.0.0.1)
docker compose -f docker-compose-dev.yml up -d

# Применение миграций схемы
alembic upgrade head
```

### 3. Запуск в Production
```bash
# Поднимает всё: Бота, API (через отдельный процесс), Postgres, Redis, Metabase
docker compose up -d --build
```

### Переменные окружения (`.env`)
Обязательные:
* `BOT_TOKEN` — токен бота от @BotFather.
* `JWT_SECRET` — секретный ключ (64+ символов) для подписи токенов Mini App.
* `WEBAPP_URL` — публичный URL фронтенда (для CORS).
* `GROQ_API_KEY`, `GEMINI_API_KEY` — ключи провайдеров.
* `DATABASE_URL`, `REDIS_URL` — строки подключения.
* `ADMIN_IDS` — ID администраторов через запятую (для скрытых команд).

---

## 🗺 Вектор развития (Roadmap)

### 🚀 Завершено (Release 1.0)
- [x] Полноценный Telegram Mini App (React) с бесшовной авторизацией.
- [x] FastAPI-бэкенд для обслуживания Mini App.
- [x] Автоматический парсинг 4 метрик настроения и продуктивности.
- [x] Глобальный аудит безопасности (Rate limiting, CORS, JWT in-memory).
- [x] Двуязычность (Русский / Английский).

### 🔄 В работе & Бэклог
- **Voice to Diary:** Поддержка голосовых сообщений (Whisper / STT).
- **Умный AI-Контекст:** Инжект предыдущих записей в промпты для глубокой персонализации ответов ИИ.
- **Smart Routing:** Переход на LiteLLM для балансировки AI-запросов.
- **Экспорт данных:** Выгрузка всего дневника в PDF/Markdown для пользователя.

---

## 📄 Лицензия

Проект разрабатывается в приватном репозитории. Все права защищены.
