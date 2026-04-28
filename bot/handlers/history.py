from aiogram import Router, types, F
from aiogram.filters import Command
from db.database import async_session
from db.queries import get_latest_diary_entry, get_adjacent_entry
from bot.keyboards.main_kb import get_history_kb

router = Router()

@router.message(Command("history"))
@router.message(F.text == "📚 Мой дневник")
async def show_history_start(message: types.Message):
    async with async_session() as session:
        latest_entry = await get_latest_diary_entry(session, message.from_user.id)
        
        if not latest_entry:
            await message.answer("Твой дневник пока пуст! Жми «📝 Записать день», чтобы начать.")
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
async def process_history_pagination(callback: types.CallbackQuery):
    # Разрезаем колбек, чтобы понять куда листать и от какого ID
    parts = callback.data.split("_")
    action = parts[1]
    current_id = int(parts[2])
    
    async with async_session() as session:
        # Ищем нужную запись
        target_entry = await get_adjacent_entry(session, callback.from_user.id, current_id, action)
        
        if not target_entry:
            await callback.answer("Дальше записей нет 🤷‍♂️", show_alert=True)
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