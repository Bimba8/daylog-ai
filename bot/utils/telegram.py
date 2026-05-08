import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
    TelegramNetworkError,
)

logger = logging.getLogger(__name__)


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
        logger.warning(f"User {chat_id} blocked the bot, skipping send")
        return False
    except TelegramRetryAfter as e:
        # Telegram просит подождать (flood control) — ждём и пробуем ещё раз
        logger.warning(f"Rate limited for {chat_id}, retrying after {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        try:
            await bot.send_message(chat_id=chat_id, **kwargs)
            return True
        except Exception as retry_err:
            logger.error(f"Retry failed for {chat_id}: {retry_err}")
            return False
    except TelegramBadRequest as e:
        # Некорректный запрос (text слишком длинный, chat не найден и т.д.)
        logger.warning(f"Bad request sending to {chat_id}: {e}")
        return False
    except TelegramNetworkError as e:
        logger.error(f"Network error sending to {chat_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to {chat_id}: {e}")
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
        logger.warning(f"Failed to delete message: {e}")
        return False
