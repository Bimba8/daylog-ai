from aiogram import Router, types, F
from aiogram.filters import StateFilter
from bot.keyboards.main_kb import get_start_diary_inline_kb

# Этот роутер регистрируется ПОСЛЕДНИМ в main.py.
# Он ловит все сообщения без активного FSM-состояния,
# которые не были обработаны другими хендлерами.
router = Router()

@router.message(F.text, StateFilter(None))
async def catch_stray_text(message: types.Message):
    await message.answer(
        "👀 <b>Текст вижу, но я не в режиме записи</b>\n\n"
        "Чтобы дневник сохранился:\n"
        "• Нажми кнопку «📝 Записать день».\n"
        "• Отправь или перешли мне этот текст еще раз.",
        reply_markup=get_start_diary_inline_kb()
    )

@router.message(StateFilter(None))
async def catch_stray_media(message: types.Message):
    await message.answer(
        "🔤 <b>Я пока понимаю только текст</b>\n\n"
        "Голосовые, фото и кружочки не пройдут. Нажми «📝 Записать день» и расскажи обо всем буквами.",
        reply_markup=get_start_diary_inline_kb()
    )
