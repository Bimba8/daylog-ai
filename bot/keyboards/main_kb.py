from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

ru_timezones = {
    "Калининград (МСК-1)": "Europe/Kaliningrad",
    "Москва (МСК)": "Europe/Moscow",
    "Самара (МСК+1)": "Europe/Samara",
    "Екатеринбург (МСК+2)": "Asia/Yekaterinburg",
    "Омск (МСК+3)": "Asia/Omsk",
    "Красноярск (МСК+4)": "Asia/Krasnoyarsk",
    "Иркутск (МСК+5)": "Asia/Irkutsk",
    "Якутск (МСК+6)": "Asia/Yakutsk",
    "Владивосток (МСК+7)": "Asia/Vladivostok",
    "Магадан (МСК+8)": "Asia/Magadan",
    "Камчатка (МСК+9)": "Asia/Kamchatka"
}

def get_main_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📝 Записать день")],
        [KeyboardButton(text="📚 Мой дневник"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="❤️ Поддержать проект"), KeyboardButton(text="⚙️ Настройки")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выбери действие..."
    )

def get_onboarding_start_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Погнали 🚀", callback_data="start_onboarding")
    return builder.as_markup()

def get_report_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📝 Записать день", callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="set_tz"))
    builder.add(InlineKeyboardButton(text="⏰ Время напоминания", callback_data="set_time"))
    builder.add(InlineKeyboardButton(text="❓ Помощь", callback_data="open_help_menu"))
    builder.add(InlineKeyboardButton(text="📰 Настройки дайджеста", callback_data="digest_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_timezone_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for btn_text, tz_str in ru_timezones.items():
        builder.add(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"tz_{tz_str}"
            )
        )
    
    builder.adjust(2)
    return builder.as_markup()

def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text="Отмена")
    return ReplyKeyboardMarkup(
        keyboard=[[kb]],
        resize_keyboard=True
    )

# FIX: BL-07 — Инлайн-кнопка «Завершить запись» вместо ненадёжного стоп-слова «пока».
# Юзер видит её под каждым ответом AI в диалоге и может нажать в любой момент.
def get_finish_diary_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Завершить запись", callback_data="finish_diary"))
    return builder.as_markup()
    
def get_history_kb(current_id: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка "В прошлое" (более старые записи, ID меньше)
    if has_prev:
        builder.add(InlineKeyboardButton(text="⬅️ Раньше", callback_data=f"hist_prev_{current_id}"))
    
    # Кнопка "В будущее" (более новые записи, ID больше)
    if has_next:
        builder.add(InlineKeyboardButton(text="Позже ➡️", callback_data=f"hist_next_{current_id}"))
        
    # Выстраиваем кнопки в один ряд (если их две)
    builder.adjust(2)
    return builder.as_markup()

def get_donate_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🪙 Крипта (EVM, SOL)", callback_data="donate_crypto"))
    builder.add(InlineKeyboardButton(text="💳 Рубли (СБП, Карты)", url="https://pay.cloudtips.ru/p/b5bcdbd6"))                           # ВСТАВИТЬ ССЫЛКУ НА CLOUDTIPS
    builder.add(InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="donate_stars"))
    
    builder.adjust(1)
    return builder.as_markup()

def get_donate_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад к способам", callback_data="donate_back"))
    return builder.as_markup()

def get_stars_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="1 ⭐️", callback_data="stars_1"))  # тест
    builder.add(InlineKeyboardButton(text="50 ⭐️", callback_data="stars_50"))
    builder.add(InlineKeyboardButton(text="100 ⭐️", callback_data="stars_100"))
    builder.add(InlineKeyboardButton(text="250 ⭐️", callback_data="stars_250"))
    builder.add(InlineKeyboardButton(text="500 ⭐️", callback_data="stars_500"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад к способам", callback_data="donate_back"))
    
    builder.adjust(3, 2, 1)            # поменять на (2, 2, 1) после удаления тест кнопки
    return builder.as_markup()

def get_start_diary_inline_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📝 Записать день", callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📅 День недели", callback_data="choose_digest_day"))
    builder.add(InlineKeyboardButton(text="🕒 Время отправки", callback_data="choose_digest_time"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_main"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_day_kb(selected_day: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    for day in range(0, 7):
        text = f"{days[day]} ✅" if day == selected_day else days[day]
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dday_{day}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_digest"))
        
    builder.adjust(3, 4, 1)
    return builder.as_markup()
    
def get_digest_time_kb(selected_time: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for time in range(0, 24, 2):
        text = f"{time}:00 ✅" if time == selected_time else f"{time}:00"
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dtime_{time}"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_digest"))
        
    builder.adjust(3)
    return builder.as_markup()