from aiogram import Router, types, F
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from urllib.parse import quote
from bot.keyboards.main_kb import get_donate_kb, get_donate_back_kb, get_stars_kb

router = Router()

MAIN_DONATE_TEXT = (
    "❤️ <b>Поддержка DayLog AI</b>\n\n"
    "Сейчас бот работает на энтузиазме, но аренда серверов, API моделей, баз данных и разработка новых крутых фич требуют времени и реальных денег.\n\n"
    "Если дневник помогает тебе наводить порядок в мыслях — буду рад любой поддержке. Выбирай удобный способ 👇"
)

CRYPTO_TEXT = (
    "🤝 <b>Спасибо за поддержку!</b>\n\n"
    "Любой перевод идет напрямую на оплату серверов и развитие бота.\n\n"
    "Нажми на адрес, чтобы скопировать:\n\n"
    "<b>EVM:</b>\n"
    "<code>0x4e6844271890e801F2666Ef73D1ba74c494FB1CC</code>\n\n"
    "<b>Solana:</b>\n"
    "<code>4u1ijqdx1Tt6ceo4FkNAR2Nh85zFSgAikSXkfAtEUuMi</code>\n\n"
    "<i>Пожалуйста, проверяйте адреса кошельков при отправке.</i>"
)

STARS_TEXT = (
    "⭐️ <b>Telegram Stars</b>\n\n"
    "Оплата в пару кликов прямо внутри мессенджера. Выбери комфортную сумму ниже 👇"
)

_HELP_TEXT = (
    "🧠 <b>Как работает DayLog AI?</b>\n\n"
    "Я — твой умный личный дневник. Больше никаких душных таблиц и оценок настроения от 1 до 10.\n\n"
    "Просто рассказывай мне, как прошел твой день, обычным текстом. А нейросеть сама проанализирует его и вытянет метрики: <i>настроение, энергию, стресс и продуктивность</i>.\n\n"
    "🎮 <b>Твой пульт управления:</b>\n"
    "• <b>Записать день</b> — написать отчет (только 1 раз в сутки)\n"
    "• <b>Мой дневник</b> — полистать прошлые записи\n"
    "• <b>Статистика</b> — посмотреть свои средние метрики\n"
    "• <b>Настройки</b> — поменять время напоминаний или таймзону\n\n"
    "<code>💡 Лайфхак: Чем больше деталей в тексте, тем точнее ИИ оценит твое состояние.</code>\n\n"
    "<i>Нашел баг или есть крутая идея? Пиши разработчику!</i>"
)


def _get_help_kb() -> InlineKeyboardMarkup:
    """Клавиатура для help-страницы с кнопками обратной связи и доната."""
    raw_text = "Здарова! Есть фидбек по DayLog AI: "
    encoded_text = quote(raw_text)
    dev_url = f"tg:resolve?domain=bimba_alpaca&text={encoded_text}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать разработчику", url=dev_url)],
        [InlineKeyboardButton(text="⭐️ Поддержать проект", callback_data="open_main_donate")]
    ])


@router.message(F.text == "❤️ Поддержать проект")
async def show_donate_menu(message: types.Message):
    await message.answer(text=MAIN_DONATE_TEXT, reply_markup=get_donate_kb())
    
@router.callback_query(F.data == "donate_crypto")
async def show_crypto_donate(callback: types.CallbackQuery):
    await callback.message.edit_text(text=CRYPTO_TEXT, reply_markup=get_donate_back_kb())
    await callback.answer()
    
@router.callback_query(F.data == "donate_back")
async def back_to_donate_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(text=MAIN_DONATE_TEXT, reply_markup=get_donate_kb())
    await callback.answer()

@router.callback_query(F.data == "donate_stars")
async def show_stars_donate(callback: types.CallbackQuery):
    await callback.message.edit_text(text=STARS_TEXT, reply_markup=get_stars_kb())
    await callback.answer()

_VALID_STAR_AMOUNTS = {1, 50, 100, 250, 500}

@router.callback_query(F.data.startswith("stars_"))
async def send_stars_invoice(callback: types.CallbackQuery):
    try:
        amount = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректные данные")
        return
    
    if amount not in _VALID_STAR_AMOUNTS:
        await callback.answer("Некорректная сумма")
        return
    
    prices = [LabeledPrice(label="⭐️ Поддержка", amount=amount)]
    await callback.message.answer_invoice(
        title="Поддержка DayLog AI",
        description="Вклад в оплату серверов и нейросетей. Делаем дневник умнее вместе! 🧠",
        payload=f"donate_stars_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await callback.answer()
    
@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    if not pre_checkout_query.invoice_payload.startswith("donate_stars_"):
        await pre_checkout_query.answer(ok=False, error_message="Неизвестный платёж")
        return
    await pre_checkout_query.answer(ok=True)
    
@router.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer(
        "🎉 <b>Оплата прошла успешно!</b>\n\n"
        "Звезды получены. Огромное спасибо за поддержку DayLog, крепко обнял! 🫂"
    )
    
@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def show_help(message: types.Message):
    await message.answer(text=_HELP_TEXT, reply_markup=_get_help_kb())

# Отправляем help новым сообщением, а не edit — безопасно для старых callback'ов.
@router.callback_query(F.data == "open_help_menu")
async def process_settings_help_btn(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(text=_HELP_TEXT, reply_markup=_get_help_kb())

@router.callback_query(F.data == "open_main_donate")
async def process_help_to_donate(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(text=MAIN_DONATE_TEXT, reply_markup=get_donate_kb())
