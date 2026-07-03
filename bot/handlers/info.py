from aiogram import Router, types, F
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.filters import Command
from urllib.parse import quote
from bot.keyboards.main_kb import get_donate_kb, get_donate_back_kb, get_stars_kb
from bot.lexicon.i18n import t, all_values

router = Router()


def _get_help_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для help-страницы с кнопками обратной связи и доната."""
    raw_text = t('info_feedback_prefill', lang)
    encoded_text = quote(raw_text)
    dev_url = f"tg:resolve?domain=bimba_alpaca&text={encoded_text}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t('kb_write_developer', lang), url=dev_url)],
        [InlineKeyboardButton(text=t('kb_support_project', lang), callback_data="open_main_donate")]
    ])


@router.message(F.text.in_(all_values('kb_donate')))
async def show_donate_menu(message: types.Message, lang: str = "ru"):
    await message.answer(
        text=t('info_donate_main', lang), 
        reply_markup=get_donate_kb(lang),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    
@router.callback_query(F.data == "donate_crypto")
async def show_crypto_donate(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.message.edit_text(text=t('info_donate_crypto', lang), reply_markup=get_donate_back_kb(lang))
    await callback.answer()
    
@router.callback_query(F.data == "donate_back")
async def back_to_donate_menu(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.message.edit_text(text=t('info_donate_main', lang), reply_markup=get_donate_kb(lang))
    await callback.answer()

@router.callback_query(F.data == "donate_stars")
async def show_stars_donate(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.message.edit_text(text=t('info_donate_stars', lang), reply_markup=get_stars_kb(lang))
    await callback.answer()

_VALID_STAR_AMOUNTS = {1, 50, 100, 250, 500}

@router.callback_query(F.data.startswith("stars_"))
async def send_stars_invoice(callback: types.CallbackQuery, lang: str = "ru"):
    try:
        amount = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer(t('info_invalid_data', lang))
        return
    
    if amount not in _VALID_STAR_AMOUNTS:
        await callback.answer(t('info_invalid_amount', lang))
        return
    
    prices = [LabeledPrice(label=t('kb_donate_support', lang), amount=amount)]
    await callback.message.answer_invoice(
        title=t('kb_donate_title', lang),
        description=t('kb_donate_description', lang),
        payload=f"donate_stars_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await callback.answer()
    
@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery, lang: str = "ru"):
    if not pre_checkout_query.invoice_payload.startswith("donate_stars_"):
        await pre_checkout_query.answer(ok=False, error_message=t('info_unknown_payment', lang))
        return
    await pre_checkout_query.answer(ok=True)
    
@router.message(F.successful_payment)
async def successful_payment(message: types.Message, lang: str = "ru"):
    await message.answer(t('info_payment_success', lang))
    
@router.message(Command("help"))
@router.message(F.text.in_(all_values('kb_help')))
async def show_help(message: types.Message, lang: str = "ru"):
    await message.answer(text=t('info_help', lang), reply_markup=_get_help_kb(lang))

# Отправляем help новым сообщением, а не edit — безопасно для старых callback'ов.
@router.callback_query(F.data == "open_help_menu")
async def process_settings_help_btn(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.answer()
    await callback.message.answer(text=t('info_help', lang), reply_markup=_get_help_kb(lang))

@router.callback_query(F.data == "open_main_donate")
async def process_help_to_donate(callback: types.CallbackQuery, lang: str = "ru"):
    await callback.answer()
    await callback.message.answer(text=t('info_donate_main', lang), reply_markup=get_donate_kb(lang))
