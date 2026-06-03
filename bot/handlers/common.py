from aiogram import Router, types, F
from aiogram.filters import StateFilter, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_start_diary_inline_kb
from db.queries import get_user, get_user_entries
from bot.services.ai import generate_weekly_digest

# Этот роутер регистрируется ПОСЛЕДНИМ в main.py.
# Он ловит все сообщения без активного FSM-состояния,
# которые не были обработаны другими хендлерами.
router = Router()

# тестовая ручка для дайджестов
@router.message(Command("test_digest"))
async def force_digest_test(message: types.Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    
    if not user:
        await message.answer("❌ Тебя нет в базе, напиши /start")
        return
        
    await message.answer("🔨 Собираю тестовый дайджест. Жди, Gemini думает...")
    
    try:
        # МАГИЯ ЗДЕСЬ: берем тупо 7 последних записей за всё время
        entries = await get_user_entries(
            session=session, 
            tg_id=message.from_user.id, 
            order="desc", # Берем с конца
            limit=7
        )
        
        if len(entries) < 2:
            await message.answer(f"⚠️ Для теста нужно минимум 2 записи. Найдено: {len(entries)}.")
            return
            
        # Скармливаем их ИИ
        digest_html = await generate_weekly_digest(entries)
        
        if digest_html:
            await message.answer(digest_html)
        else:
            await message.answer("❌ ИИ ничего не вернул или отдал кривой JSON. Чекай логи в консоли.")
            
    except Exception as e:
        await message.answer(f"❌ Критическая ошибка при генерации: {e}")

@router.message(F.text, StateFilter(None))
async def catch_stray_text(message: types.Message):
    await message.answer(
        "👀 <b>Текст вижу, но я не в режиме записи</b>\n\n"
        "Чтобы дневник сохранился:\n"
        "• Нажми кнопку «📝 Записать день».\n"
        "• Отправь или перешли мне этот текст еще раз.",
        reply_markup=get_start_diary_inline_kb()
    )

@router.message(StateFilter(None))
async def catch_stray_media(message: types.Message):
    await message.answer(
        "🔤 <b>Я пока понимаю только текст</b>\n\n"
        "Голосовые, фото и кружочки не пройдут. Нажми «📝 Записать день» и расскажи обо всем буквами.",
        reply_markup=get_start_diary_inline_kb()
    )