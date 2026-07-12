"""
Центральный модуль интернационализации.

Единая точка входа для получения локализованных строк.
Фоллбэк: если ключ не найден в целевом языке → русский → сам ключ.
"""

from bot.lexicon.ru import LEXICON_RU
from bot.lexicon.en import LEXICON_EN

_LEXICONS: dict[str, dict[str, str]] = {
    "ru": LEXICON_RU,
    "en": LEXICON_EN,
}


def t(key: str, lang: str = "ru") -> str:
    """Получить локализованную строку по ключу и языку.

    Цепочка фоллбэков: целевой язык → LEXICON_RU → сам ключ.
    """
    return _LEXICONS.get(lang, LEXICON_RU).get(key, LEXICON_RU.get(key, key))


def all_values(key: str) -> set[str]:
    """Получить значения ключа на ВСЕХ языках.

    Используется в фильтрах хендлеров для мультиязычного матчинга кнопок:
        F.text.in_(all_values('kb_write_day'))
    """
    return {lexicon[key] for lexicon in _LEXICONS.values() if key in lexicon}
