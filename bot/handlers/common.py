from aiogram import Router, types, F
from aiogram.filters import StateFilter, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_start_diary_inline_kb
from db.queries import get_user, get_user_entries
from bot.services.ai import generate_weekly_digest
from bot.lexicon.ru import LEXICON_RU

# Этот роутер регистрируется ПОСЛЕДНИМ в main.py.
# Он ловит все сообщения без активного FSM-состояния,
# которые не были обработаны другими хендлерами.
router = Router()

# тестовая ручка для дайджестов
@router.message(Command("test_digest"))
async def force_digest_test(message: types.Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    
    if not user:
        await message.answer(LEXICON_RU['common_no_user'])
        return
        
    await message.answer(LEXICON_RU['common_digest_loading'])
    
    try:
        # МАГИЯ ЗДЕСЬ: берем тупо 7 последних записей за всё время
        entries = await get_user_entries(
            session=session, 
            tg_id=message.from_user.id, 
            order="desc", # Берем с конца
            limit=7
        )
        
        if len(entries) < 2:
            await message.answer(LEXICON_RU['common_digest_min_entries'].format(count=len(entries)))
            return
            
        # Скармливаем их ИИ
        digest_html = await generate_weekly_digest(entries)
        
        if digest_html:
            await message.answer(digest_html)
        else:
            await message.answer(LEXICON_RU['common_digest_ai_empty'])
            
    except Exception as e:
        await message.answer(LEXICON_RU['common_digest_error'].format(error=e))

@router.message(F.text, StateFilter(None))
async def catch_stray_text(message: types.Message):
    await message.answer(
        LEXICON_RU['common_stray_text'],
        reply_markup=get_start_diary_inline_kb()
    )

@router.message(StateFilter(None))
async def catch_stray_media(message: types.Message):
    await message.answer(
        LEXICON_RU['common_stray_media'],
        reply_markup=get_start_diary_inline_kb()
    )