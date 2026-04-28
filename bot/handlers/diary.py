from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from bot.handlers.states import DiaryState
from db.database import async_session
from db.queries import add_diary_entry, check_today_entry
from bot.services.ai import get_ai_question
from bot.services.scheduler import schedule_nudge, cancel_nudge, schedule_night_cleaner, cancel_night_cleaner
from bot.services.saver import finalize_diary_entry
from bot.keyboards.main_kb import get_cancel_kb, get_main_kb
    
# Создаем роутер для этого файла
router = Router()

# Этот декоратор ловит команду /daylog
@router.message(Command("daylog"))
@router.message(F.text == "📝 Записать день")
async def cmd_daylog(message: types.Message, state: FSMContext):
    async with async_session() as session:
        already_wrote_today = await check_today_entry(session, message.from_user.id)
        
        if already_wrote_today:
            await message.answer("Ты сегодня уже отчитался! Отдыхай, завтра обсудим новый день. 😉")
            return
    
    await state.set_state(DiaryState.waiting_for_story)
    await message.answer(
        text="Привет! Как прошел твой день? Поделись мыслями, а я выслушаю.",
        reply_markup=get_cancel_kb()
        ) # Это пока заглушка от ИИ
    
@router.message(DiaryState.waiting_for_story)
async def process_story(message: types.Message, state: FSMContext):
    
    if len(message.text) > 1500:
        await message.answer(
            "Воу, полегче! 😅 Твой день был настолько насыщенным, что текст не влезает в мои лимиты памяти. "
            f"Давай уложимся в 1500 символов (сейчас тут {len(message.text)}). Сократи немного и отправь заново!"
        )
        return
    
    processing_msg = await message.answer("<i>Внимательно читаю и думаю...</i>") # Сообщаем юзеру, что ИИ думает (ведь запрос к OpenRouter может занять пару секунд)
    ai_response = await get_ai_question(message.text) # Отправляем текст юзера в нейросеть
    if not ai_response:
        await processing_msg.delete()
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=message.text, 
            state=state
        )
        await message.answer(
            "Блин, сервера ИИ сейчас перегружены 😔. Но не переживай, твою запись я сохранил!",
            reply_markup=get_main_kb()
        )
        return
    
    else:
        await state.update_data(story=f"User: {message.text}", last_ai_question=ai_response, turn_count=1) # юзер прислал историю, сохраняем во временную память чтобы потом записать в бд
        await state.set_state(DiaryState.waiting_for_answer) # перевод юзера на следующее состояние
        
        # Удаляем сообщение "думаю..." и отправляем реальный ответ от ИИ
        await processing_msg.delete()
        await message.answer(ai_response)
        
        # Сообщение ушло, юзер его увидел -> заводим будильник
        schedule_nudge(
            bot=message.bot,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )
        
        schedule_night_cleaner(
            bot=message.bot,
            storage=state.storage,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )

@router.message(DiaryState.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    
    if len(message.text) > 800:
        await message.answer(
            "Воу, полегче! 😅 Твой ответ слишком длинный. "
            f"Давай уложимся в 800 символов (сейчас тут {len(message.text)}). Сократи мысль и отправь заново!"
        )
        return
    
    cancel_nudge(message.from_user.id)
    cancel_night_cleaner(message.from_user.id)
    
    data = await state.get_data()
    story = data.get("story")
    last_ai_question = data.get("last_ai_question")
    turn_count = data.get("turn_count", 1)
    new_story = f"{story}\n\nAI: {last_ai_question}\n\nUser: {message.text}"
    
    if message.text.lower() == "пока": # стоп слово для завершения
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=story, 
            state=state
        )
        await message.answer(
            "Ок, понял тебя! Запись сохранена. Отличного вечера!",
            reply_markup=get_main_kb()
        )
        return
    
    elif turn_count >= 2:
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=new_story, 
            state=state
        )
        await message.answer(
            "Круто, спасибо за ответы! Всё записал в дневник.\n\n"
            "<i>Сейчас нейронка подобьет итоги твоего дня, и я их пришлю...</i>",
            reply_markup=get_main_kb()
        )
        return
    
    else:
        processing_msg = await message.answer("<i>Читаю твой ответ...</i>")
        ai_response = await get_ai_question(new_story)
        
        if not ai_response:
            await processing_msg.delete()
            await finalize_diary_entry(
                bot=message.bot, 
                chat_id=message.chat.id, 
                user_id=message.from_user.id, 
                text=new_story, 
                state=state
            )
            await message.answer(
                "Блин, сервера ИИ сейчас перегружены 😔. Но не переживай, твою запись я сохранил!",
                reply_markup=get_main_kb()
            )
            return
        
        if "?" not in ai_response:
            await processing_msg.delete()
            final_story = new_story + f"\nAI: {ai_response}"
            await finalize_diary_entry(
                bot=message.bot, 
                chat_id=message.chat.id, 
                user_id=message.from_user.id, 
                text=final_story, 
                state=state
            )
            await message.answer(ai_response, reply_markup=get_main_kb())
            return
        
        await state.update_data(
            story=new_story,
            last_ai_question=ai_response,
            turn_count=turn_count + 1
        )
        
        await processing_msg.delete()
        await message.answer(ai_response + "\n\n<i>(Напиши 'пока', чтобы завершить запись)</i>")
        
        schedule_nudge(
            bot=message.bot,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )
        
        schedule_night_cleaner(
            bot=message.bot,
            storage=state.storage,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )

# инициализация написания отчета при ежедневной напоминалке
@router.callback_query(F.data == "write_report")
async def report_from_reminder(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DiaryState.waiting_for_story)
    await callback.message.delete() 
    await callback.message.answer(  
        "Отлично! ✍️\nРасскажи, как прошел день, какие задачи закрыл?",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()
    
# Фильтр StateFilter(None) означает: "Лови сообщение ТОЛЬКО если у юзера сейчас НЕТ активных состояний"
@router.message(F.text, StateFilter(None))
async def catch_stray_text(message: types.Message):
    await message.answer(
        "Кажется, я сейчас не в режиме записи, поэтому не могу сохранить этот текст. 🤔\n\n"
        "💡 <b>Как сохранить отчет:</b>\n"
        "Нажми кнопку <b>«📝 Записать день»</b> в меню внизу экрана, а затем просто скопируй и отправь мне этот текст снова."
    )
    
