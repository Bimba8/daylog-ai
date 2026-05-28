from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.handlers.states import DiaryState
from db.queries import add_diary_entry, check_today_entry, get_or_create_user
from bot.services.ai import get_ai_response
from bot.services.scheduler import schedule_nudge, cancel_nudge, schedule_night_cleaner, cancel_night_cleaner
from bot.services.saver import finalize_diary_entry
from bot.keyboards.main_kb import get_cancel_kb, get_main_kb, get_finish_diary_kb
from bot.utils.telegram import safe_delete
    
router = Router()


@router.message(Command("daylog"))
@router.message(F.text == "📝 Записать день")
async def cmd_daylog(message: types.Message, state: FSMContext, session: AsyncSession):
    """Начало записи дневника. Проверяет, не писал ли юзер сегодня."""
    user, _ = await get_or_create_user(session, message.from_user.id)
    already_wrote_today = await check_today_entry(session, message.from_user.id, user.timezone)
    
    if already_wrote_today:
        await message.answer(
            "🛡 <b>Отчет за сегодня уже в базе</b>\n\n"
            "На сегодня всё. Отдыхай, а новый день обсудим завтра!"
        )
        return
    
    await state.set_state(DiaryState.waiting_for_story)
    await state.update_data(user_tz=user.timezone)
    await message.answer(
        text=(
            "✍️ <b>Время рефлексии</b>\n\n"
            "Как прошел день? Какие задачи закрыл, что по настроению? Пиши всё как есть."
        ),
        reply_markup=get_cancel_kb()
        )
     

@router.message(DiaryState.waiting_for_story)
async def process_story(message: types.Message, state: FSMContext, session: AsyncSession):
    """Обработка первого сообщения юзера (рассказ о дне)."""
    if not message.text:
        await message.answer(
            "🔤 <b>Жду именно текст</b>\n\n"
            "Фото, стикеры и войсы пока не перевариваю. Напиши словами!"
        )
        return
    
    if len(message.text) > 1500:
        await message.answer(
            f"✂️ <b>Слишком много букв!</b>\n\n"
            f"Я перевариваю тексты только до <code>1500</code> символов (сейчас тут <code>{len(message.text)}</code>).\n"
            f"Сократи текст и отправь заново."
        )
        return
    
    # Processing lock: блокируем повторные сообщения, пока AI думает
    data = await state.get_data()
    if data.get("ai_processing"):
        await message.answer("⏳ <b>Подожди</b>\n\nЯ ещё обрабатываю предыдущее сообщение.")
        return
    await state.update_data(ai_processing=True)
    
    processing_msg = await message.answer("🧠 <i>Анализирую твой день...</i>")
    ai_response = await get_ai_response(message.text)
    await state.update_data(ai_processing=False)
    
    if not ai_response:
        await safe_delete(processing_msg)
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=message.text, 
            state=state,
            session=session
        )
        await message.answer(
            text=(
                "⚠️ <b>Сервера ИИ прилегли отдохнуть</b>\n\n"
                "Твой текст я <b>сохранил</b> в базу, ничего не потерялось, но ответить на него прямо сейчас не смогу."
            ),
            reply_markup=get_main_kb()
        )
        return
    
    else:
        await state.update_data(story=f"User: {message.text}", last_ai_question=ai_response, turn_count=1)
        await state.set_state(DiaryState.waiting_for_answer)
        
        await safe_delete(processing_msg)
        # Инлайн-кнопка «Завершить запись» под каждым ответом AI
        await message.answer(ai_response, reply_markup=get_finish_diary_kb())
        
        schedule_nudge(
            bot=message.bot,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )
        
        fsm_data = await state.get_data()
        user_tz = fsm_data.get("user_tz", "Europe/Moscow")
        
        schedule_night_cleaner(
            bot=message.bot,
            storage=state.storage,
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            tz_str=user_tz
        )

@router.message(DiaryState.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext, session: AsyncSession):
    """Обработка ответов юзера в диалоге с AI (до 2 раундов)."""
    if not message.text:
        await message.answer(
            "🔤 <b>Жду именно текст</b>\n\n"
            "Фото, стикеры и войсы пока не перевариваю. Напиши словами!"
        )
        return
    
    if len(message.text) > 800:
        await message.answer(
            f"✂️ <b>Слишком много букв!</b>\n\n"
            f"Я перевариваю тексты только до <code>800</code> символов (сейчас тут <code>{len(message.text)}</code>).\n"
            f"Сократи мысль и отправь заново."
        )
        return
    
    # Processing lock: блокируем повторные сообщения, пока AI думает
    data = await state.get_data()
    if data.get("ai_processing"):
        await message.answer("⏳ <b>Подожди</b>\n\nЯ ещё обрабатываю предыдущее сообщение.")
        return
    
    cancel_nudge(message.from_user.id)
    cancel_night_cleaner(message.from_user.id)
    
    story = data.get("story")
    last_ai_question = data.get("last_ai_question")
    turn_count = data.get("turn_count", 1)
    new_story = f"{story}\n\nAI: {last_ai_question}\n\nUser: {message.text}"
    
    if message.text.lower() == "пока":
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=story, 
            state=state,
            session=session
        )
        await message.answer(
            text=(
                "💾 <b>Запись сохранена</b>\n\n"
                "Отличного вечера!"
            ),
            reply_markup=get_main_kb()
        )
        return
    
    elif turn_count >= 2:
        loading_msg = await message.answer("💾 <b>Всё записал в дневник</b>\n\n<i>Сейчас нейронка подобьет итоги дня, секунду...</i>", reply_markup=get_main_kb())
        await finalize_diary_entry(
            bot=message.bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            text=new_story, 
            state=state,
            session=session,
            loading_msg_id=loading_msg.message_id
        )
        return
    
    else:
        await state.update_data(ai_processing=True)
        processing_msg = await message.answer("🧠 <i>Анализирую твой ответ...</i>")
        ai_response = await get_ai_response(new_story)
        await state.update_data(ai_processing=False)
        
        if not ai_response:
            await safe_delete(processing_msg)
            # Отменяем фоновые задачи, чтобы не сработали после finalize
            cancel_nudge(message.from_user.id)
            cancel_night_cleaner(message.from_user.id)
            await finalize_diary_entry(
                bot=message.bot, 
                chat_id=message.chat.id, 
                user_id=message.from_user.id, 
                text=new_story, 
                state=state,
                session=session
            )
            await message.answer(
                text=(
                    "⚠️ <b>Сервера ИИ прилегли отдохнуть</b>\n\n"
                    "Твой текст я <b>сохранил</b> в базу, ничего не потерялось, но ответить на него прямо сейчас не смогу."
                ),
                reply_markup=get_main_kb()
            )
            return
        
        # Диалог продолжается до кнопки «Завершить» или лимита раундов.
        await state.update_data(
            story=new_story,
            last_ai_question=ai_response,
            turn_count=turn_count + 1
        )
        
        await safe_delete(processing_msg)
        await message.answer(ai_response, reply_markup=get_finish_diary_kb())
        
        schedule_nudge(
            bot=message.bot,
            user_id=message.from_user.id,
            chat_id=message.chat.id
        )
        
        user_tz = data.get("user_tz", "Europe/Moscow")
        
        schedule_night_cleaner(
            bot=message.bot,
            storage=state.storage,
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            tz_str=user_tz
        )

# Завершение диалога по инлайн-кнопке. Работает в обоих FSM-состояниях.
@router.callback_query(F.data == "finish_diary")
async def finish_diary_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Явное завершение записи через инлайн-кнопку."""
    current_state = await state.get_state()
    
    if current_state not in (DiaryState.waiting_for_story, DiaryState.waiting_for_answer):
        await callback.answer("Запись уже завершена")
        return
    
    cancel_nudge(callback.from_user.id)
    cancel_night_cleaner(callback.from_user.id)
    
    data = await state.get_data()
    story = data.get("story", "")
    
    if not story:
        await state.clear()
        await callback.answer("Нет текста для сохранения")
        return
    
    # 1. Сначала гасим инлайн-кнопку, чтобы юзер не тыкал второй раз
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # 2. Отправляем заглушку И запоминаем её ID
    loading_msg = await callback.message.answer(
        text="💾 <b>Всё записал в дневник</b>\n\n<i>Сейчас нейронка подобьет итоги дня, секунду...</i>",
        reply_markup=get_main_kb()
    )
    
    # 3. Переносим вызов finalize_diary_entry ниже и прокидываем ID
    await finalize_diary_entry(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        text=story,
        state=state,
        session=session,
        loading_msg_id=loading_msg.message_id  # <--- Передаем ID нашей заглушки
    )
    
    await callback.answer()

# Инициализация записи по напоминалке
@router.callback_query(F.data == "write_report")
async def report_from_reminder(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало записи через инлайн-кнопку (из напоминалки или меню)."""
    user, _ = await get_or_create_user(session, callback.from_user.id)
    
    await state.set_state(DiaryState.waiting_for_story)
    await state.update_data(user_tz=user.timezone)
    await callback.message.delete() 
    await callback.message.answer(  
        text=(
            "✍️ <b>Отлично, давай запишем</b>\n\n"
            "Как прошел день? Какие задачи закрыл, что по настроению? Пиши всё как есть."
        ),
        reply_markup=get_cancel_kb()
    )
    await callback.answer()
