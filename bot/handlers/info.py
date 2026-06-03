from aiogram import Router, types, F
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.filters import Command
from urllib.parse import quote
from bot.keyboards.main_kb import get_donate_kb, get_donate_back_kb, get_stars_kb

router = Router()

MAIN_DONATE_TEXT = (
    "⭐️ <b>Поддержка DayLog AI</b>\n\n"
    "Привет! Я <a href='https://t.me/bimba_alpaca'>Bimba</a>, создатель DayLog 🧠\n\n"
    "Сейчас этот дневник — мой личный пет-проект, который держится на чистом энтузиазме. "
    "Я пилю его в свободное время, изучаю новые технологии и очень хочу довести задумку до полноценного крутого продукта.\n\n"
    "Но реальность такова, что развитие и стабильная работа бота требуют затрат: аренда серверов, оплата API нейросетей, "
    "подписки на ИИ и инструменты для разработки, ну и, конечно же, энергетики для ночного кодинга.\n\n"
    "Если ты хочешь поддержать меня и развитие DayLog, я буду очень благодарен. "
    "Любой донат — это вклад в развитие DayLog и крутая мотивация для меня делать его еще лучше.\n\n"
    "<i>Выбери удобный способ ниже</i> 👇"
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
    "🧠 <b>Что такое DayLog AI?</b>\n\n"
    "Это личный дневник, который делает всю работу за тебя. Никаких ручных трекеров и душных оценок.\n\n"
    "<b>Как мы взаимодействуем:</b>\n"
    "1. <b>Запись:</b> Просто выгружаешь мысли текстом — как прошел день, что бесит или радует.\n"
    "2. <b>Диалог:</b> Я могу задать пару уточняющих вопросов, чтобы помочь тебе порефлексировать. Отвечать не обязательно — диалог всегда можно скипнуть.\n"
    "3. <b>Анализ:</b> Бот фоном вытянет из текста твои метрики: <i>настроение, энергию, стресс и продуктивность</i>.\n"
    "4. <b>Дайджест:</b> Раз в неделю я собираю умное саммари. Нейросеть проанализирует все твои записи, найдет скрытые паттерны, подсветит утечки ресурса и выдаст инсайты.\n\n"
    "🕹 <b>Навигация:</b>\n"
    "• <b>Записать день</b> — старт рефлексии (1 раз в сутки)\n"
    "• <b>Мой дневник</b> — архив твоих записей\n"
    "• <b>Статистика</b> — графики твоего состояния\n"
    "• <b>Настройки</b> — таймзона и расписание дайджеста\n\n"
    "💡 <code>Лайфхак: Чем больше искренности и деталей, тем глубже и точнее будет твой еженедельный дайджест.</code>\n\n"
    "Нашел баг или придумал фичу? Пиши разработчику 👇"
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
    await message.answer(
        text=MAIN_DONATE_TEXT, 
        reply_markup=get_donate_kb(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    
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
        description="Вклад в стабильную работу и развитие бота.",
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
