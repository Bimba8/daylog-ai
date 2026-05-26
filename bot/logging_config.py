"""
Централизованная конфигурация логирования на базе loguru.

Вызов: setup_logging() один раз из main.py до создания бота.
Все модули получают типизированный логгер через logger.bind(module="...").

Цветовая схема (main sink — по уровню):
  ERROR/CRITICAL — красный
  WARNING       — жёлтый
  INFO/SUCCESS  — зелёный
  DEBUG         — серый/белый

Отдельный sink для DB — всё в cyan.
"""

import sys
import logging
import inspect
from pathlib import Path

from loguru import logger
from config import config


# ─── InterceptHandler: мост stdlib logging → loguru ───────────────────────
# Перехватывает вызовы из SQLAlchemy, aiogram, APScheduler и любых
# библиотек, использующих стандартный logging, и прокидывает их в loguru.

class InterceptHandler(logging.Handler):
    """Перенаправляет записи стандартного logging в loguru.
    
    Автоматически определяет module-тег по имени логгера:
      sqlalchemy.* → DB
      apscheduler.* → SCHEDULER
      aiogram.* → AIOGRAM
      всё остальное → SYSTEM
    """

    # Маппинг: префикс имени stdlib-логгера → module-тег для loguru
    _MODULE_MAP = {
        "sqlalchemy": "DB",
        "apscheduler": "SCHEDULER",
        "aiogram": "AIOGRAM",
        "aiohttp": "AIOGRAM",
    }

    def _resolve_module(self, logger_name: str) -> str:
        """Определяет module-тег по имени stdlib-логгера."""
        for prefix, module in self._MODULE_MAP.items():
            if logger_name.startswith(prefix):
                return module
        return "SYSTEM"

    def emit(self, record: logging.LogRecord) -> None:
        # Определяем уровень loguru по имени (если есть) или по числовому значению
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Поднимаемся по стеку вызовов, чтобы loguru показал реальный caller,
        # а не InterceptHandler.emit
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        # Определяем module по имени оригинального логгера
        module = self._resolve_module(record.name)

        logger.bind(module=module).opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# ─── Форматы ─────────────────────────────────────────────────────────────

# Основной формат: цвет уровня определяется loguru автоматически
# ERROR/CRITICAL → красный, WARNING → жёлтый, INFO → зелёный, DEBUG → белый
MAIN_FORMAT = (
    "<green>{time:HH:mm:ss}</green> │ "
    "<level>{level:<8}</level> │ "
    "<level>{extra[module]:<12}</level> │ "
    "<level>{message}</level>"
)

# DB-sink: всё в cyan, чтобы SQL визуально отделялся от бизнес-логики
DB_FORMAT = (
    "<green>{time:HH:mm:ss}</green> │ "
    "<cyan>{level:<8}</cyan> │ "
    "<cyan>{extra[module]:<12}</cyan> │ "
    "<cyan>{message}</cyan>"
)

# Файловый лог: без цветовых тегов
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} │ "
    "{level:<8} │ "
    "{extra[module]:<12} │ "
    "{message}"
)


def _is_db_module(record: dict) -> bool:
    """Фильтр: пропускает только записи с module='DB'."""
    return record["extra"].get("module") == "DB"


def _is_not_db_module(record: dict) -> bool:
    """Фильтр: пропускает всё, кроме module='DB'."""
    return record["extra"].get("module") != "DB"


def setup_logging() -> None:
    """Инициализация системы логирования.
    
    Вызывается ОДИН раз из main.py, до создания Bot/Dispatcher.
    Потокобезопасна (loguru внутри использует thread-lock).
    """
    log_level = config.LOG_LEVEL.upper()

    # 1. Убираем дефолтный sink loguru (stderr без форматирования)
    logger.remove()

    # 2. Устанавливаем дефолтный module для записей без bind()
    logger.configure(extra={"module": "SYSTEM"})

    # 3. Main sink — stderr, всё кроме DB
    logger.add(
        sys.stderr,
        format=MAIN_FORMAT,
        level=log_level,
        filter=_is_not_db_module,
        colorize=True,
        backtrace=True,
        diagnose=False,  # В проде не показываем значения переменных в traceback
    )

    # 4. DB sink — stderr, только DB (cyan-формат)
    logger.add(
        sys.stderr,
        format=DB_FORMAT,
        level=log_level,
        filter=_is_db_module,
        colorize=True,
        backtrace=True,
        diagnose=False,
    )

    # 5. Файловый лог с ротацией
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "daylog.log",
        format=FILE_FORMAT,
        level=log_level,
        rotation="10 MB",     # Ротация при 10 МБ
        retention="7 days",   # Хранить 7 дней
        compression="gz",     # Сжимать старые логи
        encoding="utf-8",
        backtrace=True,
        diagnose=False,
    )

    # 6. Перехват стандартного logging → loguru
    #    InterceptHandler автоматически маппит имя логгера → module-тег
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 7. Тонкая настройка SQLAlchemy логгеров
    #    По умолчанию WARNING — SQL не засоряет поток.
    #    При DB_ECHO=True — открываем INFO, чтобы видеть запросы.
    sa_level = logging.INFO if config.DB_ECHO else logging.WARNING

    for sa_logger_name in ("sqlalchemy.engine", "sqlalchemy.pool"):
        sa_logger = logging.getLogger(sa_logger_name)
        sa_logger.handlers = [InterceptHandler()]
        sa_logger.propagate = False
        sa_logger.setLevel(sa_level)

    # 8. Приглушаем шумные библиотеки
    for noisy_logger in ("aiohttp.access", "apscheduler.scheduler", "apscheduler.executors"):
        nl = logging.getLogger(noisy_logger)
        nl.handlers = [InterceptHandler()]
        nl.propagate = False
        nl.setLevel(logging.WARNING)

    logger.bind(module="BOOT").info(
        "Логгер инициализирован (уровень={}, файл=logs/daylog.log)", log_level
    )
