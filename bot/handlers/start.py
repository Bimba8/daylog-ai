from datetime import datetime
from bot.utils import validate_time  # FIX: CQ-01 — DRY: общая утилита валидации времени
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_or_create_user, update_user_timezone, update_user_time, update_user_digest_day, update_user_digest_time
from bot.keyboards.main_kb import get_main_kb, get_settings_menu_kb, get_timezone_kb, get_onboarding_start_kb, get_report_kb, ru_timezones, get_digest_day_kb, get_digest_time_kb, get_digest_settings_menu_kb
from bot.handlers.states import SettingState, OnboardingState
from bot.services.scheduler import schedule_daily_reminder


router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext, session: AsyncSession):
    # FIX: BL-01 + BL-02 — Сбрасываем FSM при /start, чтобы юзер не застрял в старом состоянии.
    # Без этого: юзер в середине DiaryState нажимает /start → видит приветствие,
    # но FSM остаётся в DiaryState → следующее сообщение уйдёт в process_answer вместо ожидаемого.
    await state.clear()
    user, is_new = await get_or_create_user(
        session=session,
        tg_id=message.from_user.id,
        username=message.from_user.username
    )
    
    photo = FSInputFile("assets/onboarding.png")
    
    welcome_text = (
        "🧠 <b>Привет! Я DayLog</b>\n\n"
        "Твой умный личный дневник. Забудь про скучные трекеры — просто рассказывай мне, как прошел день, а я сделаю всё остальное:\n\n"
        "• Разложу мысли по полочкам\n"
        "• Вытяну метрики (настроение, стресс, энергия, продуктивность)\n"
        "• Соберу красивую статистику\n\n"
        "Готов навести порядок в голове? Настройка займет ровно 10 секунд!"
    )
    if is_new:
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=get_onboarding_start_kb()
        )
    else:
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=get_report_kb()
        )
    
@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OnboardingState.waiting_for_tz) # Переводим в ожидание часового пояса
    await callback.message.delete()
    # Меняем приветственное сообщение на вопрос про город
    await callback.message.answer(
        text=(
            "🌍 <b>Где ты находишься?</b>\n\n"
            "Выбери свой часовой пояс ниже. Это нужно, чтобы напоминалки приходили вовремя."
        ),
        reply_markup=get_timezone_kb()
    )
    await callback.answer()
    
@router.callback_query(OnboardingState.waiting_for_tz, F.data.startswith("tz_"))
async def onboarding_tz_selected(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    selected_tz = callback.data[3:]
    friendly_name = next((name for name, tz in ru_timezones.items() if tz == selected_tz), selected_tz)
    
    await update_user_timezone(session, callback.from_user.id, selected_tz)
        
    await state.set_state(OnboardingState.waiting_for_time)
    
    await callback.message.edit_text(
        text=(
            f"🌍 <b>Пояс: {friendly_name}</b>\n\n"
            f"В какое время тебе удобно подводить итоги дня?\n"
            f"Отправь время в формате <code>ЧЧ:ММ</code> (например, <code>21:00</code>)."
        )
    )
    await callback.answer()
    
@router.message(OnboardingState.waiting_for_time)
async def onboarding_time_selected(message: types.Message, state: FSMContext, session: AsyncSession):
    # FIX: CQ-01 — Используем общую утилиту вместо дублированного try/except
    new_time = validate_time(message.text)
    if new_time is None:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Напиши время цифрами в формате <code>ЧЧ:ММ</code> (от <code>00:00</code> до <code>23:59</code>)."
        )
        return
    
    user = await update_user_time(session, message.from_user.id, new_time)
    schedule_daily_reminder(
        bot=message.bot,
        user_id=user.telegram_id,
        time_str=user.reminder_time,
        tz_str=user.timezone
    )
            
    await state.clear()
    
    final_text = (
        f"✅ <b>Всё готово!</b>\n\n"
        f"Я буду приходить за отчетами каждый день ровно в <b>{new_time}</b>.\n\n"
        f"<code>⚠️ Важно: Записать день можно только 1 раз. Постарайся уместить все мысли в одно сообщение.</code>\n\n"
        f"Жми кнопку «📝 Записать день», чтобы сделать первую запись 👇"
    )
    
    await message.answer(
        text=final_text, 
        reply_markup=get_report_kb()
    )
    

# FIX: BL-01 — Обработка не-текстовых сообщений во время онбординга.
# Если юзер отправит стикер/фото вместо времени — хендлер onboarding_time_selected
# не поймает этот update (он работает только с text), и FSM зависнет.
@router.message(OnboardingState.waiting_for_time, ~F.text)
async def onboarding_non_text(message: types.Message):
    await message.answer(
        "🔤 <b>Жду именно текст</b>\n\n"
        "Отправь время в формате <code>ЧЧ:ММ</code> (например, <code>21:00</code>)."
    )

@router.message(SettingState.waiting_for_time, ~F.text)
async def setting_non_text(message: types.Message):
    await message.answer(
        "🔤 <b>Жду именно текст</b>\n\n"
        "Отправь время в формате <code>ЧЧ:ММ</code> (например, <code>21:00</code>)."
    )
    

@router.message(F.text == "⚙️ Настройки")
@router.callback_query(F.data == "settings_main")
async def show_settings_menu(event: types.Message | types.CallbackQuery):
    text = "⚙️ <b>Настройки</b>\n\nЧто будем менять?"
    kb = get_settings_menu_kb()
    
    if isinstance(event, types.Message):
        await event.answer(text=text, reply_markup=kb)
    else:
        await event.message.edit_text(text=text, reply_markup=kb)
        await event.answer()

@router.callback_query(F.data == "set_tz")
async def start_tz_selection(callback: types.CallbackQuery, state: FSMContext):
    # Включаем «режим ожидания» выбора города
    await state.set_state(SettingState.waiting_for_tz)
    
    # Редактируем старое сообщение: меняем текст и вешаем новую клавиатуру (с городами)
    await callback.message.edit_text(
        text="🌍 <b>Часовой пояс</b>\n\nГде ты сейчас находишься?",
        reply_markup=get_timezone_kb()
    )
    
    await callback.answer()
    
@router.callback_query(SettingState.waiting_for_tz, F.data.startswith("tz_"))
async def tz_selection_final(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    # 1. Вытаскиваем название пояса из callback_data
    # Мы отрезаем первые 3 символа ("tz_"), остается только "Europe/Moscow" и т.д.
    selected_tz = callback.data[3:]
    
    friendly_name = next((name for name, tz in ru_timezones.items() if tz == selected_tz), selected_tz)
    
    # 2. Убираем часики (обязательно!)
    await callback.answer(f"Выбран пояс: {friendly_name}")
    
    # 3. Сохраняем в базу данных
    user = await update_user_timezone(session, callback.from_user.id, selected_tz)
    schedule_daily_reminder(
        bot=callback.bot, 
        user_id=user.telegram_id, 
        time_str=user.reminder_time, 
        tz_str=user.timezone
    )
    
    await callback.message.edit_text(
        text=f"🌍 <b>Часовой пояс обновлен!</b>\n\nТеперь ты я работаю по времени: <b>{friendly_name}</b>."
    )
    await state.clear()
    
@router.callback_query(F.data == "set_time")
async def start_time_selection(callback: types.CallbackQuery, state: FSMContext):
    # Включаем «режим ожидания» ввода цифр
    await state.set_state(SettingState.waiting_for_time)
    
    # Редактируем сообщение: просим написать время
    await callback.message.edit_text(
        text=(
            "🕒 <b>Время напоминаний</b>\n\n"
            "Отправь желаемое время в формате <code>ЧЧ:ММ</code> (например, <code>21:00</code>)."
        ),
        reply_markup=None
    )
    
    await callback.answer()
    
@router.message(SettingState.waiting_for_time)
async def process_setting_time(message: types.Message, state: FSMContext, session: AsyncSession):
    # FIX: CQ-01 — Используем общую утилиту вместо дублированного try/except
    new_time = validate_time(message.text)
    if new_time is None:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Напиши время цифрами в формате <code>ЧЧ:ММ</code> (от <code>00:00</code> до <code>23:59</code>)."
        )
        return
    
    user = await update_user_time(session, message.from_user.id, new_time)
    schedule_daily_reminder(
        bot=message.bot,
        user_id=user.telegram_id, 
        time_str=user.reminder_time, 
        tz_str=user.timezone
    )
            
    await message.answer(
        f"🕒 <b>Время сохранено!</b>\n\n"
        f"Буду приходить за отчетом каждый день ровно в <b>{new_time}</b>."
    )
    await state.clear()
    
@router.message(Command("cancel"))
@router.message(F.text == "Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        text="🚫 <b>Действие отменено</b>",
        reply_markup=get_main_kb(),
    )

@router.callback_query(F.data == "digest_menu")
@router.callback_query(F.data == "settings_digest")
async def show_digest_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="⚙️ Настройки дайджеста. Что будем менять?",
        reply_markup=get_digest_settings_menu_kb()
    )
    
@router.callback_query(F.data == "choose_digest_day")
async def show_digest_day_selection(callback: types.CallbackQuery, session: AsyncSession):
    user, _ = await get_or_create_user(session, callback.from_user.id)
    await callback.message.edit_text(
        text="📅 Выбери день недели для получения дайджеста:",
        reply_markup=get_digest_day_kb(user.digest_day)
    )

@router.callback_query(F.data == "choose_digest_time")
async def show_digest_time_selection(callback: types.CallbackQuery, session: AsyncSession):
    user, _ = await get_or_create_user(session, callback.from_user.id)
    await callback.message.edit_text(
        text="🕒 Выбери время отправки дайджеста:",
        reply_markup=get_digest_time_kb(user.digest_time)
    )

@router.callback_query(F.data.startswith("dday_"))
async def process_digest_day(callback: types.CallbackQuery, session: AsyncSession):
    day_idx = int(callback.data.split("_")[1])
    user = await update_user_digest_day(session, callback.from_user.id, day_idx)
    new_kb = get_digest_day_kb(selected_day=day_idx)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except TelegramBadRequest:
        # Игнорируем, если клавиатура не изменилась
        pass
    await callback.answer()
    
@router.callback_query(F.data.startswith("dtime_"))
async def process_digest_time(callback: types.CallbackQuery, session: AsyncSession):
    time_idx = int(callback.data.split("_")[1])
    user = await update_user_digest_time(session, callback.from_user.id, time_idx)
    new_kb = get_digest_time_kb(selected_time=time_idx)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except TelegramBadRequest:
        # Игнорируем, если клавиатура не изменилась
        pass
    await callback.answer()