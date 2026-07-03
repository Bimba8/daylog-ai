from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_latest_diary_entry, get_adjacent_entry
from bot.keyboards.main_kb import get_history_kb, get_report_kb
from bot.lexicon.i18n import t, all_values

router = Router()

@router.message(Command("history"))
@router.message(F.text.in_(all_values('kb_my_diary')))
async def show_history_start(message: types.Message, session: AsyncSession, lang: str = "ru"):
    latest_entry = await get_latest_diary_entry(session, message.from_user.id)
    
    if not latest_entry:
        await message.answer(
            text=t('hist_empty', lang),
            reply_markup=get_report_kb(lang)
        )
        return
    
    prev_entry = await get_adjacent_entry(session, message.from_user.id, latest_entry.id, "prev")
    has_prev = bool(prev_entry)
    has_next = False
    
    date_str = latest_entry.created_at.strftime("%d.%m.%Y")
    text = t('hist_entry', lang).format(date=date_str, text=latest_entry.user_text)
    
    await message.answer(
        text=text,
        reply_markup=get_history_kb(latest_entry.id, has_prev, has_next, lang)
    )
        
@router.callback_query(F.data.startswith("hist_"))
async def process_history_pagination(callback: types.CallbackQuery, session: AsyncSession, lang: str = "ru"):
    """Пагинация записей дневника с валидацией callback_data."""
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer(t('hist_invalid_data', lang))
        return
    
    action = parts[1]
    try:
        current_id = int(parts[2])
    except ValueError:
        await callback.answer(t('hist_invalid_data', lang))
        return
    
    target_entry = await get_adjacent_entry(session, callback.from_user.id, current_id, action)
    
    if not target_entry:
        await callback.answer(t('hist_no_more', lang), show_alert=True)
        return
    
    # Проверяем соседей У НОВОЙ записи
    prev_entry = await get_adjacent_entry(session, callback.from_user.id, target_entry.id, "prev")
    next_entry = await get_adjacent_entry(session, callback.from_user.id, target_entry.id, "next")
    
    date_str = target_entry.created_at.strftime("%d.%m.%Y")
    new_text = t('hist_entry', lang).format(date=date_str, text=target_entry.user_text)
    
    await callback.message.edit_text(
        text=new_text,
        reply_markup=get_history_kb(
            current_id=target_entry.id,
            has_prev=bool(prev_entry),
            has_next=bool(next_entry),
            lang=lang
        )
    )
    
    await callback.answer()