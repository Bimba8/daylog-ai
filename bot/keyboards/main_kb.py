from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.lexicon.i18n import t

# Таймзоны — callback_data не зависит от языка, маппинг по IANA-ключам.
_tz_keys = [
    ("kb_tz_kaliningrad", "Europe/Kaliningrad"),
    ("kb_tz_moscow", "Europe/Moscow"),
    ("kb_tz_samara", "Europe/Samara"),
    ("kb_tz_yekaterinburg", "Asia/Yekaterinburg"),
    ("kb_tz_omsk", "Asia/Omsk"),
    ("kb_tz_krasnoyarsk", "Asia/Krasnoyarsk"),
    ("kb_tz_irkutsk", "Asia/Irkutsk"),
    ("kb_tz_yakutsk", "Asia/Yakutsk"),
    ("kb_tz_vladivostok", "Asia/Vladivostok"),
    ("kb_tz_magadan", "Asia/Magadan"),
    ("kb_tz_kamchatka", "Asia/Kamchatka"),
]

_tz_keys_en = [
    ("UTC-12:00", "Etc/GMT+12"),
    ("UTC-11:00", "Etc/GMT+11"),
    ("UTC-10:00", "Etc/GMT+10"),
    ("UTC-09:00", "Etc/GMT+9"),
    ("UTC-08:00", "Etc/GMT+8"),
    ("UTC-07:00", "Etc/GMT+7"),
    ("UTC-06:00", "Etc/GMT+6"),
    ("UTC-05:00", "Etc/GMT+5"),
    ("UTC-04:00", "Etc/GMT+4"),
    ("UTC-03:00", "Etc/GMT+3"),
    ("UTC-02:00", "Etc/GMT+2"),
    ("UTC-01:00", "Etc/GMT+1"),
    ("UTC+00:00", "UTC"),
    ("UTC+01:00", "Etc/GMT-1"),
    ("UTC+02:00", "Etc/GMT-2"),
    ("UTC+03:00", "Etc/GMT-3"),
    ("UTC+04:00", "Etc/GMT-4"),
    ("UTC+05:00", "Etc/GMT-5"),
    ("UTC+06:00", "Etc/GMT-6"),
    ("UTC+07:00", "Etc/GMT-7"),
    ("UTC+08:00", "Etc/GMT-8"),
    ("UTC+09:00", "Etc/GMT-9"),
    ("UTC+10:00", "Etc/GMT-10"),
    ("UTC+11:00", "Etc/GMT-11"),
    ("UTC+12:00", "Etc/GMT-12"),
    ("UTC+13:00", "Etc/GMT-13"),
    ("UTC+14:00", "Etc/GMT-14"),
]

# Единый список всех валидных таймзон для проверки (и русских, и английских)
valid_timezones = set([tz for _, tz in _tz_keys] + [tz for _, tz in _tz_keys_en])

# Обратный маппинг: IANA → friendly name (для обоих языков)
def get_tz_friendly_name(iana_tz: str, lang: str = "ru") -> str:
    """Получить человекочитаемое имя таймзоны по IANA-коду."""
    if lang == "en":
        for label, tz_str in _tz_keys_en:
            if tz_str == iana_tz:
                return label
                
    for lex_key, tz_str in _tz_keys:
        if tz_str == iana_tz:
            return t(lex_key, lang)
    return iana_tz

def get_main_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=t('kb_write_day', lang))],
        [KeyboardButton(text=t('kb_donate', lang)), KeyboardButton(text=t('kb_help', lang))]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t('kb_placeholder', lang)
    )

def get_onboarding_start_kb(lang: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(text=t('kb_onboarding_go', lang), callback_data="start_onboarding")
    return builder.as_markup()

def get_report_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_write_day', lang), callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_settings_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_tz', lang), callback_data="set_tz"))
    builder.add(InlineKeyboardButton(text=t('kb_reminder_time', lang), callback_data="set_time"))
    builder.add(InlineKeyboardButton(text=t('kb_digest_settings', lang), callback_data="digest_menu"))
    builder.add(InlineKeyboardButton(text=t('kb_help', lang), callback_data="open_help_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_timezone_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if lang == "en":
        for label, tz_str in _tz_keys_en:
            builder.add(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"tz_{tz_str}"
                )
            )
        builder.adjust(3)
    else:
        for lex_key, tz_str in _tz_keys:
            builder.add(
                InlineKeyboardButton(
                    text=t(lex_key, lang),
                    callback_data=f"tz_{tz_str}"
                )
            )
        builder.adjust(2)
        
    return builder.as_markup()

def get_cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text=t('kb_cancel', lang))
    return ReplyKeyboardMarkup(
        keyboard=[[kb]],
        resize_keyboard=True
    )

# Инлайн-кнопка завершения записи, отображается под каждым ответом AI.
def get_finish_diary_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_finish_diary', lang), callback_data="finish_diary"))
    return builder.as_markup()
    
def get_history_kb(current_id: int, has_prev: bool, has_next: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка "В прошлое" (более старые записи, ID меньше)
    if has_prev:
        builder.add(InlineKeyboardButton(text=t('kb_history_prev', lang), callback_data=f"hist_prev_{current_id}"))
    
    # Кнопка "В будущее" (более новые записи, ID больше)
    if has_next:
        builder.add(InlineKeyboardButton(text=t('kb_history_next', lang), callback_data=f"hist_next_{current_id}"))
        
    # Выстраиваем кнопки в один ряд (если их две)
    builder.adjust(2)
    return builder.as_markup()

def get_donate_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text=t('kb_donate_crypto', lang), callback_data="donate_crypto"))
    builder.add(InlineKeyboardButton(text=t('kb_donate_rub', lang), url="https://pay.cloudtips.ru/p/b5bcdbd6"))
    builder.add(InlineKeyboardButton(text=t('kb_donate_stars', lang), callback_data="donate_stars"))
    
    builder.adjust(1)
    return builder.as_markup()

def get_donate_back_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_donate_back', lang), callback_data="donate_back"))
    return builder.as_markup()

def get_stars_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="1 ⭐️", callback_data="stars_1"))  # тест
    builder.add(InlineKeyboardButton(text="50 ⭐️", callback_data="stars_50"))
    builder.add(InlineKeyboardButton(text="100 ⭐️", callback_data="stars_100"))
    builder.add(InlineKeyboardButton(text="250 ⭐️", callback_data="stars_250"))
    builder.add(InlineKeyboardButton(text="500 ⭐️", callback_data="stars_500"))
    builder.add(InlineKeyboardButton(text=t('kb_donate_back', lang), callback_data="donate_back"))
    
    builder.adjust(3, 2, 1)            # поменять на (2, 2, 1) после удаления тест кнопки
    return builder.as_markup()

def get_start_diary_inline_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_write_day', lang), callback_data="write_report"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_settings_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=t('kb_digest_day', lang), callback_data="choose_digest_day"))
    builder.add(InlineKeyboardButton(text=t('kb_digest_time', lang), callback_data="choose_digest_time"))
    builder.add(InlineKeyboardButton(text=t('kb_back', lang), callback_data="settings_main"))
    builder.adjust(1)
    return builder.as_markup()

def get_digest_day_kb(selected_day: int | None = None, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    day_keys = [
        'kb_day_monday', 'kb_day_tuesday', 'kb_day_wednesday',
        'kb_day_thursday', 'kb_day_friday', 'kb_day_saturday',
        'kb_day_sunday'
    ]
    
    for day in range(0, 7):
        label = t(day_keys[day], lang)
        text = f"{label} ✅" if day == selected_day else label
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dday_{day}"))
    builder.add(InlineKeyboardButton(text=t('kb_back', lang), callback_data="settings_digest"))
        
    builder.adjust(3, 4, 1)
    return builder.as_markup()
    
def get_digest_time_kb(selected_time: int | None = None, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for time in range(0, 24, 2):
        text = f"{time}:00 ✅" if time == selected_time else f"{time}:00"
        builder.add(InlineKeyboardButton(text=text, callback_data=f"dtime_{time}"))
    builder.add(InlineKeyboardButton(text=t('kb_back', lang), callback_data="settings_digest"))
        
    builder.adjust(3)
    return builder.as_markup()

def get_language_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка (онбординг). Текст билингвальный — не локализуется."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))
    builder.add(InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"))
    builder.adjust(2)
    return builder.as_markup()