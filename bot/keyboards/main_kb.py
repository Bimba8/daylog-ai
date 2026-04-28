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
        [KeyboardButton(text="⚙️ Настройки")]
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
    kb = KeyboardButton(text="❌ Отмена")
    return ReplyKeyboardMarkup(
        keyboard=[[kb]],
        resize_keyboard=True
    )
    
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
