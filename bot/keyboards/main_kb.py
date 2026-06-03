from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.lexicon.ru import LEXICON_RU

ru_timezones = {
    LEXICON_RU['kb_tz_kaliningrad']: "Europe/Kaliningrad",
    LEXICON_RU['kb_tz_moscow']: "Europe/Moscow",
    LEXICON_RU['kb_tz_samara']: "Europe/Samara",
    LEXICON_RU['kb_tz_yekaterinburg']: "Asia/Yekaterinburg",
    LEXICON_RU['kb_tz_omsk']: "Asia/Omsk",
    LEXICON_RU['kb_tz_krasnoyarsk']: "Asia/Krasnoyarsk",
    LEXICON_RU['kb_tz_irkutsk']: "Asia/Irkutsk",
    LEXICON_RU['kb_tz_yakutsk']: "Asia/Yakutsk",
    LEXICON_RU['kb_tz_vladivostok']: "Asia/Vladivostok",
    LEXICON_RU['kb_tz_magadan']: "Asia/Magadan",
    LEXICON_RU['kb_tz_kamchatka']: "Asia/Kamchatka"
}

def get_main_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=LEXICON_RU['kb_write_day'])],
        [KeyboardButton(text=LEXICON_RU['kb_my_diary']), KeyboardButton(text=LEXICON_RU['kb_stats'])],
        [KeyboardButton(text=LEXICON_RU['kb_donate']), KeyboardButton(text=LEXICON_RU['kb_settings'])]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=LEXICON_RU['kb_placeholder']
    )

def get_onboarding_start_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text=LEXICON_RU['kb_onboarding_go'], callback_data="start_onboarding")
    return builder.as_markup()

def get_report_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_write_day'], callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_tz'], callback_data="set_tz"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_reminder_time'], callback_data="set_time"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_digest_settings'], callback_data="digest_menu"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_help'], callback_data="open_help_menu"))
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
    kb = KeyboardButton(text=LEXICON_RU['kb_cancel'])
    return ReplyKeyboardMarkup(
        keyboard=[[kb]],
        resize_keyboard=True
    )

# Инлайн-кнопка завершения записи, отображается под каждым ответом AI.
def get_finish_diary_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_finish_diary'], callback_data="finish_diary"))
    return builder.as_markup()
    
def get_history_kb(current_id: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка "В прошлое" (более старые записи, ID меньше)
    if has_prev:
        builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_history_prev'], callback_data=f"hist_prev_{current_id}"))
    
    # Кнопка "В будущее" (более новые записи, ID больше)
    if has_next:
        builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_history_next'], callback_data=f"hist_next_{current_id}"))
        
    # Выстраиваем кнопки в один ряд (если их две)
    builder.adjust(2)
    return builder.as_markup()

def get_donate_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_donate_crypto'], callback_data="donate_crypto"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_donate_rub'], url="https://pay.cloudtips.ru/p/b5bcdbd6"))                           # ВСТАВИТЬ ССЫЛКУ НА CLOUDTIPS
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_donate_stars'], callback_data="donate_stars"))
    
    builder.adjust(1)
    return builder.as_markup()

def get_donate_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_donate_back'], callback_data="donate_back"))
    return builder.as_markup()

def get_stars_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="1 ⭐️", callback_data="stars_1"))  # тест
    builder.add(InlineKeyboardButton(text="50 ⭐️", callback_data="stars_50"))
    builder.add(InlineKeyboardButton(text="100 ⭐️", callback_data="stars_100"))
    builder.add(InlineKeyboardButton(text="250 ⭐️", callback_data="stars_250"))
    builder.add(InlineKeyboardButton(text="500 ⭐️", callback_data="stars_500"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_donate_back'], callback_data="donate_back"))
    
    builder.adjust(3, 2, 1)            # поменять на (2, 2, 1) после удаления тест кнопки
    return builder.as_markup()

def get_start_diary_inline_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_write_day'], callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_digest_day'], callback_data="choose_digest_day"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_digest_time'], callback_data="choose_digest_time"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_back'], callback_data="settings_main"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_day_kb(selected_day: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    days = [
        LEXICON_RU['kb_day_monday'], LEXICON_RU['kb_day_tuesday'], LEXICON_RU['kb_day_wednesday'],
        LEXICON_RU['kb_day_thursday'], LEXICON_RU['kb_day_friday'], LEXICON_RU['kb_day_saturday'],
        LEXICON_RU['kb_day_sunday']
    ]
    
    for day in range(0, 7):
        text = f"{days[day]} ✅" if day == selected_day else days[day]
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dday_{day}"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_back'], callback_data="settings_digest"))
        
    builder.adjust(3, 4, 1)
    return builder.as_markup()
    
def get_digest_time_kb(selected_time: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for time in range(0, 24, 2):
        text = f"{time}:00 ✅" if time == selected_time else f"{time}:00"
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dtime_{time}"))
    builder.add(InlineKeyboardButton(text=LEXICON_RU['kb_back'], callback_data="settings_digest"))
        
    builder.adjust(3)
    return builder.as_markup()