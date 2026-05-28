from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_latest_diary_entry, get_adjacent_entry
from bot.keyboards.main_kb import get_history_kb, get_report_kb

router = Router()

@router.message(Command("history"))
@router.message(F.text == "📚 Мой дневник")
async def show_history_start(message: types.Message, session: AsyncSession):
    latest_entry = await get_latest_diary_entry(session, message.from_user.id)
    
    if not latest_entry:
        await message.answer(
            text=(
                "📭 <b>Дневник пока пуст</b>\n\n"
                "Здесь будут храниться твои записи. Нажми «📝 Записать день», чтобы сделать первую."
            ),
            reply_markup=get_report_kb()
        )
        return
    
    prev_entry = await get_adjacent_entry(session, message.from_user.id, latest_entry.id, "prev")
    has_prev = bool(prev_entry)
    has_next = False
    
    date_str = latest_entry.created_at.strftime("%d.%m.%Y")
    text = f"📅 <b>Запись от {date_str}</b>\n\n{latest_entry.user_text}"
    
    await message.answer(
        text=text,
        reply_markup=get_history_kb(latest_entry.id, has_prev, has_next)
    )
        
@router.callback_query(F.data.startswith("hist_"))
async def process_history_pagination(callback: types.CallbackQuery, session: AsyncSession):
    """Пагинация записей дневника с валидацией callback_data."""
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Некорректные данные")
        return
    
    action = parts[1]
    try:
        current_id = int(parts[2])
    except ValueError:
        await callback.answer("Некорректные данные")
        return
    
    target_entry = await get_adjacent_entry(session, callback.from_user.id, current_id, action)
    
    if not target_entry:
        await callback.answer("🛑 Дальше записей нет", show_alert=True)
        return
    
    # Проверяем соседей У НОВОЙ записи
    prev_entry = await get_adjacent_entry(session, callback.from_user.id, target_entry.id, "prev")
    next_entry = await get_adjacent_entry(session, callback.from_user.id, target_entry.id, "next")
    
    date_str = target_entry.created_at.strftime("%d.%m.%Y")
    new_text = f"📅 <b>Запись от {date_str}</b>\n\n{target_entry.user_text}"
    
    await callback.message.edit_text(
        text=new_text,
        reply_markup=get_history_kb(
            current_id=target_entry.id,
            has_prev=bool(prev_entry),
            has_next=bool(next_entry)
        )
    )
    
    await callback.answer()