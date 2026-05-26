import asyncio
from loguru import logger
from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
    TelegramNetworkError,
)

logger = logger.bind(module="TELEGRAM")


# FIX: CRIT-05 — Без этой обёртки любой заблокировавший бота юзер ронял шедулер/хендлер
# необработанным TelegramForbiddenError, а rate limit от Telegram останавливал весь event loop.
async def safe_send(bot: Bot, chat_id: int, **kwargs) -> bool:
    """
    Безопасная отправка сообщения. Перехватывает все ошибки Telegram API.
    Возвращает True если сообщение отправлено, False если нет.
    Используется в scheduler и фоновых задачах, где падение недопустимо.
    """
    try:
        await bot.send_message(chat_id=chat_id, **kwargs)
        return True
    except TelegramForbiddenError:
        # Юзер заблокировал бота — отправка невозможна, просто пропускаем
        logger.warning("Юзер {} заблокировал бота, пропуск отправки", chat_id)
        return False
    except TelegramRetryAfter as e:
        # Telegram просит подождать (flood control) — ждём и пробуем ещё раз
        logger.warning("Rate limit для {}, повтор через {}с", chat_id, e.retry_after)
        await asyncio.sleep(e.retry_after)
        try:
            await bot.send_message(chat_id=chat_id, **kwargs)
            return True
        except Exception as retry_err:
            logger.error("Повторная отправка для {} не удалась: {}", chat_id, retry_err)
            return False
    except TelegramBadRequest as e:
        # Некорректный запрос (text слишком длинный, chat не найден и т.д.)
        logger.warning("Некорректный запрос для {}: {}", chat_id, e)
        return False
    except TelegramNetworkError as e:
        logger.error("Сетевая ошибка отправки для {}: {}", chat_id, e)
        return False
    except Exception as e:
        logger.error("Неожиданная ошибка отправки для {}: {}", chat_id, e)
        return False


# FIX: CRIT-05 — Без этой обёртки processing_msg.delete() падал,
# если юзер успел удалить сообщение вручную или оно уже истекло.
async def safe_delete(message) -> bool:
    """Безопасное удаление сообщения (игнорирует если уже удалено или недоступно)."""
    try:
        await message.delete()
        return True
    except (TelegramBadRequest, TelegramForbiddenError):
        return False
    except Exception as e:
        logger.warning("Не удалось удалить сообщение: {}", e)
        return False
