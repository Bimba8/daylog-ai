from aiogram import Router, types, F
from aiogram.filters import StateFilter, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_start_diary_inline_kb
from db.queries import get_user, get_user_entries
from bot.services.ai import generate_weekly_digest
from bot.lexicon.i18n import t
from loguru import logger
from config import config

# Этот роутер регистрируется ПОСЛЕДНИМ в main.py.
# Он ловит все сообщения без активного FSM-состояния,
# которые не были обработаны другими хендлерами.
router = Router()

_ADMIN_IDS: set[int] = set()
for _id_str in config.ADMIN_IDS.split(","):
    _id_str = _id_str.strip()
    if _id_str.isdigit():
        _ADMIN_IDS.add(int(_id_str))

# тестовая ручка для дайджестов — только для админов
@router.message(Command("test_digest"))
async def force_digest_test(message: types.Message, session: AsyncSession, lang: str = "ru"):
    if message.from_user.id not in _ADMIN_IDS:
        return
    user = await get_user(session, message.from_user.id)
    
    if not user:
        await message.answer(t('common_no_user', lang))
        return
    
    lang = user.language_code or lang
    await message.answer(t('common_digest_loading', lang))
    
    try:
        # МАГИЯ ЗДЕСЬ: берем тупо 7 последних записей за всё время
        entries = await get_user_entries(
            session=session, 
            tg_id=message.from_user.id, 
            order="desc", # Берем с конца
            limit=7
        )
        
        if len(entries) < 2:
            await message.answer(t('common_digest_min_entries', lang).format(count=len(entries)))
            return
            
        # Скармливаем их ИИ
        digest_html = await generate_weekly_digest(entries, lang=lang)
        
        if digest_html:
            await message.answer(digest_html)
        else:
            await message.answer(t('common_digest_ai_empty', lang))
            
    except Exception as e:
        logger.error("Ошибка генерации тестового дайджеста для {}: {}", message.from_user.id, e)
        await message.answer(t('common_digest_error', lang).format(error="Внутренняя ошибка сервера"))

@router.message(F.text, StateFilter(None))
async def catch_stray_text(message: types.Message, lang: str = "ru"):
    await message.answer(
        t('common_stray_text', lang),
        reply_markup=get_start_diary_inline_kb(lang)
    )

@router.message(StateFilter(None))
async def catch_stray_media(message: types.Message, lang: str = "ru"):
    await message.answer(
        t('common_stray_media', lang),
        reply_markup=get_start_diary_inline_kb(lang)
    )