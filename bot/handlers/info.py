from aiogram import Router, types, F
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.filters import Command
from urllib.parse import quote
from bot.keyboards.main_kb import get_donate_kb, get_donate_back_kb, get_stars_kb
from bot.lexicon.ru import LEXICON_RU

router = Router()


def _get_help_kb() -> InlineKeyboardMarkup:
    """Клавиатура для help-страницы с кнопками обратной связи и доната."""
    raw_text = LEXICON_RU['info_feedback_prefill']
    encoded_text = quote(raw_text)
    dev_url = f"tg:resolve?domain=bimba_alpaca&text={encoded_text}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_RU['kb_write_developer'], url=dev_url)],
        [InlineKeyboardButton(text=LEXICON_RU['kb_support_project'], callback_data="open_main_donate")]
    ])


@router.message(F.text == LEXICON_RU['kb_donate'])
async def show_donate_menu(message: types.Message):
    await message.answer(
        text=LEXICON_RU['info_donate_main'], 
        reply_markup=get_donate_kb(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    
@router.callback_query(F.data == "donate_crypto")
async def show_crypto_donate(callback: types.CallbackQuery):
    await callback.message.edit_text(text=LEXICON_RU['info_donate_crypto'], reply_markup=get_donate_back_kb())
    await callback.answer()
    
@router.callback_query(F.data == "donate_back")
async def back_to_donate_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(text=LEXICON_RU['info_donate_main'], reply_markup=get_donate_kb())
    await callback.answer()

@router.callback_query(F.data == "donate_stars")
async def show_stars_donate(callback: types.CallbackQuery):
    await callback.message.edit_text(text=LEXICON_RU['info_donate_stars'], reply_markup=get_stars_kb())
    await callback.answer()

_VALID_STAR_AMOUNTS = {1, 50, 100, 250, 500}

@router.callback_query(F.data.startswith("stars_"))
async def send_stars_invoice(callback: types.CallbackQuery):
    try:
        amount = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer(LEXICON_RU['info_invalid_data'])
        return
    
    if amount not in _VALID_STAR_AMOUNTS:
        await callback.answer(LEXICON_RU['info_invalid_amount'])
        return
    
    prices = [LabeledPrice(label=LEXICON_RU['kb_donate_support'], amount=amount)]
    await callback.message.answer_invoice(
        title=LEXICON_RU['kb_donate_title'],
        description=LEXICON_RU['kb_donate_description'],
        payload=f"donate_stars_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await callback.answer()
    
@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    if not pre_checkout_query.invoice_payload.startswith("donate_stars_"):
        await pre_checkout_query.answer(ok=False, error_message=LEXICON_RU['info_unknown_payment'])
        return
    await pre_checkout_query.answer(ok=True)
    
@router.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer(LEXICON_RU['info_payment_success'])
    
@router.message(Command("help"))
@router.message(F.text == LEXICON_RU['kb_help'])
async def show_help(message: types.Message):
    await message.answer(text=LEXICON_RU['info_help'], reply_markup=_get_help_kb())

# Отправляем help новым сообщением, а не edit — безопасно для старых callback'ов.
@router.callback_query(F.data == "open_help_menu")
async def process_settings_help_btn(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(text=LEXICON_RU['info_help'], reply_markup=_get_help_kb())

@router.callback_query(F.data == "open_main_donate")
async def process_help_to_donate(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(text=LEXICON_RU['info_donate_main'], reply_markup=get_donate_kb())
