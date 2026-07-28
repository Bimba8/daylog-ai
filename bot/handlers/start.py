from datetime import datetime
from bot.utils import validate_time
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_or_create_user, update_user_timezone, update_user_time, update_user_digest_day, update_user_digest_time, update_user_language
from bot.keyboards.main_kb import (
    get_main_kb, get_settings_menu_kb, get_timezone_kb, get_onboarding_start_kb,
    get_report_kb, get_digest_day_kb, get_digest_time_kb,
    get_digest_settings_menu_kb, get_language_kb, get_tz_friendly_name, valid_timezones
)
from bot.handlers.states import SettingState, OnboardingState
from bot.services.scheduler import schedule_daily_reminder
from bot.lexicon.i18n import t, all_values


router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext, session: AsyncSession, lang: str = "ru"):
    # Сброс FSM, чтобы /start всегда начинал с чистого состояния
    await state.clear()
    user, is_new = await get_or_create_user(
        session=session,
        tg_id=message.from_user.id,
        username=message.from_user.username
    )
    
    if is_new:
        # Новый пользователь → сначала выбор языка
        await state.set_state(OnboardingState.choosing_language)
        await message.answer(
            text=t('start_choose_language', lang),
            reply_markup=get_language_kb()
        )
    else:
        # Существующий пользователь → показываем приветствие на его языке
        lang = user.language_code or "ru"
        photo = FSInputFile("assets/onboarding.png")
        await message.answer_photo(
            photo=photo,
            caption=t('start_welcome', lang),
            reply_markup=get_report_kb(lang)
        )

# ── Онбординг: выбор языка ────────────────────────────────────────────
@router.callback_query(OnboardingState.choosing_language, F.data.startswith("lang_"))
async def onboarding_language_selected(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = callback.data.split("_")[1]  # "ru" или "en"
    if lang not in ("ru", "en"):
        await callback.answer(t('start_invalid_data', "ru"))
        return
    await update_user_language(session, callback.from_user.id, lang)
    await state.update_data(lang=lang)

    photo = FSInputFile("assets/onboarding.png")
    await callback.message.delete()

    await callback.message.answer_photo(
        photo=photo,
        caption=t('start_welcome', lang),
        reply_markup=get_onboarding_start_kb(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(callback: types.CallbackQuery, state: FSMContext, lang: str = "ru"):
    await state.set_state(OnboardingState.waiting_for_tz)
    # Достаём lang из FSM data (если он там), иначе из middleware
    data = await state.get_data()
    lang = data.get("lang", lang)
    await callback.message.delete()

    await callback.message.answer(
        text=t('start_onboarding_tz', lang),
        reply_markup=get_timezone_kb(lang)
    )
    await callback.answer()
    
@router.callback_query(OnboardingState.waiting_for_tz, F.data.startswith("tz_"))
async def onboarding_tz_selected(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "ru"):
    selected_tz = callback.data[3:]
    if selected_tz not in valid_timezones:
        await callback.answer(t('start_invalid_data', lang))
        return
    data = await state.get_data()
    lang = data.get("lang", lang)
    
    await update_user_timezone(session, callback.from_user.id, selected_tz)
    
    # Устанавливаем дефолтное время напоминания 20:00
    default_time = "20:00"
    user = await update_user_time(session, callback.from_user.id, default_time)
    
    schedule_daily_reminder(
        bot=callback.bot,
        user_id=user.telegram_id,
        time_str=user.reminder_time,
        tz_str=user.timezone
    )
            
    await state.clear()
    
    await callback.message.edit_text(
        text=t('start_onboarding_done', lang).format(time=default_time), 
        reply_markup=get_report_kb(lang)
    )
    await callback.answer()

@router.message(SettingState.waiting_for_time, ~F.text)
async def setting_non_text(message: types.Message, lang: str = "ru"):
    await message.answer(t('start_text_only_time', lang))
    

@router.message(F.text.in_(all_values('kb_settings')))
@router.callback_query(F.data == "settings_main")
async def show_settings_menu(event: types.Message | types.CallbackQuery, lang: str = "ru"):
    text = t('start_settings_title', lang)
    kb = get_settings_menu_kb(lang)
    
    if isinstance(event, types.Message):
        await event.answer(text=text, reply_markup=kb)
    else:
        await event.message.edit_text(text=text, reply_markup=kb)
        await event.answer()

@router.callback_query(F.data == "set_tz")
async def start_tz_selection(callback: types.CallbackQuery, state: FSMContext, lang: str = "ru"):
    # Включаем режим ожидания выбора таймзоны
    await state.set_state(SettingState.waiting_for_tz)
    
    await callback.message.edit_text(
        text=t('start_tz_select', lang),
        reply_markup=get_timezone_kb(lang)
    )
    
    await callback.answer()
    
@router.callback_query(SettingState.waiting_for_tz, F.data.startswith("tz_"))
async def tz_selection_final(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, lang: str = "ru"):
    selected_tz = callback.data[3:]
    if selected_tz not in valid_timezones:
        await callback.answer(t('start_invalid_data', lang))
        return
    
    friendly_name = get_tz_friendly_name(selected_tz, lang)
    
    await callback.answer(t('start_tz_selected_toast', lang).format(tz_name=friendly_name))
    
    user = await update_user_timezone(session, callback.from_user.id, selected_tz)
    schedule_daily_reminder(
        bot=callback.bot, 
        user_id=user.telegram_id, 
        time_str=user.reminder_time, 
        tz_str=user.timezone
    )
    
    await callback.message.edit_text(
        text=t('start_tz_updated', lang).format(tz_name=friendly_name)
    )
    await state.clear()
    
@router.callback_query(F.data == "set_time")
async def start_time_selection(callback: types.CallbackQuery, state: FSMContext, lang: str = "ru"):
    # Включаем режим ожидания ввода времени
    await state.set_state(SettingState.waiting_for_time)
    
    await callback.message.edit_text(
        text=t('start_time_prompt', lang),
        reply_markup=None
    )
    
    await callback.answer()
    
@router.message(SettingState.waiting_for_time)
async def process_setting_time(message: types.Message, state: FSMContext, session: AsyncSession, lang: str = "ru"):
    # Валидация формата ЧЧ:ММ
    new_time = validate_time(message.text)
    if new_time is None:
        await message.answer(t('start_invalid_time', lang))
        return
    
    user = await update_user_time(session, message.from_user.id, new_time)
    schedule_daily_reminder(
        bot=message.bot,
        user_id=user.telegram_id, 
        time_str=user.reminder_time, 
        tz_str=user.timezone
    )
            
    await message.answer(
        t('start_time_saved', lang).format(time=new_time)
    )
    await state.clear()
    
@router.message(Command("cancel"))
@router.message(F.text.in_(all_values('kb_cancel')))
async def cancel_handler(message: types.Message, state: FSMContext, lang: str = "ru"):
    current_state = await state.get_state()
    
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        text=t('start_cancelled', lang),
        reply_markup=get_main_kb(lang),
    )

@router.callback_query(F.data == "digest_menu")
@router.callback_query(F.data == "settings_digest")
async def show_digest_settings(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.message.edit_text(
        text=t('start_digest_settings', lang),
        reply_markup=get_digest_settings_menu_kb(lang)
    )
    
@router.callback_query(F.data == "choose_digest_day")
async def show_digest_day_selection(callback: types.CallbackQuery, session: AsyncSession, lang: str = "ru"):
    user, _ = await get_or_create_user(session, callback.from_user.id)
    await callback.message.edit_text(
        text=t('start_digest_day_select', lang),
        reply_markup=get_digest_day_kb(user.digest_day, lang)
    )

@router.callback_query(F.data == "choose_digest_time")
async def show_digest_time_selection(callback: types.CallbackQuery, session: AsyncSession, lang: str = "ru"):
    user, _ = await get_or_create_user(session, callback.from_user.id)
    await callback.message.edit_text(
        text=t('start_digest_time_select', lang),
        reply_markup=get_digest_time_kb(user.digest_time, lang)
    )

@router.callback_query(F.data.startswith("dday_"))
async def process_digest_day(callback: types.CallbackQuery, session: AsyncSession, lang: str = "ru"):
    """Обработка выбора дня дайджеста с валидацией callback_data."""
    try:
        day_idx = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer(t('start_invalid_data', lang))
        return
    if day_idx not in range(7):
        await callback.answer(t('start_invalid_day', lang))
        return
    
    user = await update_user_digest_day(session, callback.from_user.id, day_idx)
    new_kb = get_digest_day_kb(selected_day=day_idx, lang=lang)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except TelegramBadRequest:
        pass
    await callback.answer()
    
@router.callback_query(F.data.startswith("dtime_"))
async def process_digest_time(callback: types.CallbackQuery, session: AsyncSession, lang: str = "ru"):
    """Обработка выбора времени дайджеста с валидацией callback_data."""
    try:
        time_idx = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer(t('start_invalid_data', lang))
        return
    if time_idx not in range(0, 24, 2):
        await callback.answer(t('start_invalid_time_value', lang))
        return
    
    user = await update_user_digest_time(session, callback.from_user.id, time_idx)
    new_kb = get_digest_time_kb(selected_time=time_idx, lang=lang)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except TelegramBadRequest:
        pass
    await callback.answer()