from datetime import datetime
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from db.database import async_session
from db.queries import get_or_create_user, update_user_timezone, update_user_time
from bot.keyboards.main_kb import get_main_kb, get_settings_menu_kb, get_timezone_kb, get_onboarding_start_kb, ru_timezones
from bot.handlers.states import SettingState, OnboardingState
from bot.services.scheduler import schedule_daily_reminder, schedule_weekly_digest


router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        
    schedule_weekly_digest(message.bot, message.from_user.id)
    
    welcome_text = (
        "Привет! Я <b>Daylog</b> — умный дневник, с которым реально интересно разговаривать. 🧠\n\n"
        "Забудь про скучные заметки. Ты просто рассказываешь мне, как прошел твой день, а под капотом происходит магия:\n\n"
        "🤝 <b>Осмысление:</b> Я задам пару точных вопросов, чтобы помочь разложить мысли по полочкам.\n"
        "📊 <b>Оцифровка жизни:</b> ИИ сам вытянет из текста твои скрытые метрики: \n😌 Настроение, ⚡️ Энергия, 🧠 Продуктивность и 🌪 Стресс.\n"
        "📈 <b>Инсайты:</b> Я соберу всё это в наглядную статистику и буду присылать мощный еженедельный дайджест.\n\n"
        "Готов навести порядок в голове? Настройка займет ровно 10 секунд!"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_onboarding_start_kb()
    )
    
@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OnboardingState.waiting_for_tz) # Переводим в ожидание часового пояса
    
    # Меняем приветственное сообщение на вопрос про город
    await callback.message.edit_text(
        text="Для начала: где ты находишься? Мне нужно это знать, чтобы напоминалки приходили вовремя.",
        reply_markup=get_timezone_kb()
    )
    await callback.answer()
    
@router.callback_query(OnboardingState.waiting_for_tz, F.data.startswith("tz_"))
async def onboarding_tz_selected(callback: types.CallbackQuery, state: FSMContext):
    selected_tz = callback.data[3:]
    friendly_name = next((name for name, tz in ru_timezones.items() if tz == selected_tz), selected_tz)
    
    async with async_session() as session:
        await update_user_timezone(session, callback.from_user.id, selected_tz)
        
    await state.set_state(OnboardingState.waiting_for_time)
    
    await callback.message.edit_text(
        text=(
            f"Супер, {friendly_name}! 🌍\n\n"
            "В какое время тебе удобно подводить итоги дня? Напиши время в формате ЧЧ:ММ (например: 21:00)."
        )
    )
    await callback.answer()
    
@router.message(OnboardingState.waiting_for_time)
async def onboarding_time_selected(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    
    try:
        # Питон сам проверит, реальное ли это время (Часы:Минуты)
        datetime.strptime(new_time, "%H:%M")
    except ValueError:
        await message.answer("Бро, напиши реальное время в формате ЧЧ:ММ (от 00:00 до 23:59).")
        return
    
    async with async_session() as session:
        user = await update_user_time(session, message.from_user.id, new_time)
        if user:
            schedule_daily_reminder(
                bot=message.bot,
                user_id=user.telegram_id,
                time_str=user.reminder_time,
                tz_str=user.timezone
            )
            
    await state.clear()
    
    final_text = (
        f"✅ Всё готово! Я буду приходить за отчетами каждый день в {new_time}.\n\n"
        "⚠️ <b>Важное правило:</b> Записать день можно только один раз. Постарайся уместить все мысли в одно сообщение.\n\n"
        "А теперь — самое время сделать первую запись! Жми кнопку <b>«📝 Записать день»</b> в меню ниже 👇"
    )
    
    await message.answer(text=final_text, reply_markup=get_main_kb())
    

@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: types.Message):
    await message.answer(
        text="Что именно ты хочешь настроить?",
        reply_markup=get_settings_menu_kb()
    )

@router.callback_query(F.data == "set_tz")
async def start_tz_selection(callback: types.CallbackQuery, state: FSMContext):
    # Включаем «режим ожидания» выбора города
    await state.set_state(SettingState.waiting_for_tz)
    
    # Редактируем старое сообщение: меняем текст и вешаем новую клавиатуру (с городами)
    await callback.message.edit_text(
        text="Выбери свой часовой пояс:",
        reply_markup=get_timezone_kb()
    )
    
    await callback.answer()
    
@router.callback_query(F.data.startswith("tz_"))
async def tz_selection_final(callback: types.CallbackQuery, state: FSMContext):
    # 1. Вытаскиваем название пояса из callback_data
    # Мы отрезаем первые 3 символа ("tz_"), остается только "Europe/Moscow" и т.д.
    selected_tz = callback.data[3:]
    
    friendly_name = next((name for name, tz in ru_timezones.items() if tz == selected_tz), selected_tz)
    
    # 2. Убираем часики (обязательно!)
    await callback.answer(f"Выбран пояс: {friendly_name}")
    
    # 3. Сохраняем в базу данных
    async with async_session() as session:
        user = await update_user_timezone(session, callback.from_user.id, selected_tz)
        
        # Если база вернула юзера, обновляем ему будильник
        if user:
            schedule_daily_reminder(
                bot=callback.bot, 
                user_id=user.telegram_id, 
                time_str=user.reminder_time, 
                tz_str=user.timezone
            )
    
    await callback.message.edit_text(
        text=f"✅ Часовой пояс успешно изменен на {friendly_name}.\nТеперь напоминания будут приходить вовремя!"
    )
    await state.clear()
    
@router.callback_query(F.data == "set_time")
async def start_time_selection(callback: types.CallbackQuery, state: FSMContext):
    # Включаем «режим ожидания» ввода цифр
    await state.set_state(SettingState.waiting_for_time)
    
    # Редактируем сообщение: просим написать время
    await callback.message.edit_text(
        text="Введи время, когда мне тебе напоминать.\nФормат — 24 часа, например: 21:00",
        reply_markup=None                  # Убираем инлайн-кнопки совсем
    )
    
    await callback.answer()
    
@router.message(SettingState.waiting_for_time)
async def process_setting_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    
    try:
        # Питон сам проверит, реальное ли это время (Часы:Минуты)
        datetime.strptime(new_time, "%H:%M")
    except ValueError:
        await message.answer("Бро, напиши реальное время в формате ЧЧ:ММ (от 00:00 до 23:59).")
        return
    
    async with async_session() as session:
        user = await update_user_time(session, message.from_user.id, new_time)
        
        if user:
            schedule_daily_reminder(
                bot=message.bot,
                user_id=user.telegram_id, 
                time_str=user.reminder_time, 
                tz_str=user.timezone
            )
            
    await message.answer(f"✅ Ок! Теперь я буду приходить за отчетом в {new_time} по твоему времени.")
    await state.clear()
    
@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        text="Действие отменено",
        reply_markup=get_main_kb(),
    )