import json
import openai
import asyncio
from openai import AsyncOpenAI
from config import config

API_KEY = config.OPENROUTER_API_KEY
PRIMARY_MODEL = "z-ai/glm-4.5-air:free"
BACKUP_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"
BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """
Ты — близкий, эмпатичный друг, с которым человек делится итогами дня в Telegram. 
Пиши на естественном, живом русском языке без использования англицизмов (если нет прямой необходимости) и выдуманных слов.
Избегай книжных оборотов и канцеляризмов, общайся как внимательный и эмпатичный друг.
Твоя цель — выслушать, поддержать диалог и помочь человеку отрефлексировать день. Тебе передается история текущего диалога.
Строго соблюдай грамматику русского языка, следи за падежами и окончаниями

ТВОИ СТРОГИЕ ПРАВИЛА:
1. КРАТКОСТЬ. Максимум 3-4 предложения. Никаких полотен текста.
2. ЭМПАТИЯ БЕЗ СОВЕТОВ. Покажи, что услышал человека (1-2 живых предложения поддержки). Не читай нотации, не давай оценок и не пытайся "решить" его проблемы, если он не просит.
3. ТОН И СТИЛЬ. Общайся на "ты", используй повседневный язык. БУДЬ ЕСТЕСТВЕННЫМ: категорически запрещено переигрывать со сленгом (не спамь словами "бро", "чувак" и т.д.) и использовать канцелярит.
4. ПРАВИЛО ВОПРОСА. Основываясь на последнем сообщении юзера, задай ровно ОДИН мягкий, уточняющий вопрос. Запрещено задавать несколько вопросов, делать списки и повторять то, что ты уже спрашивал.
5. ИСКЛЮЧЕНИЕ ДЛЯ ПРОЩАНИЙ. Если человек прощается, говорит, что устал, идет спать или ставит точку в диалоге — просто пожелай ему отличного отдыха или спокойной ночи. В ЭТОМ СЛУЧАЕ ВОПРОС ЗАДАВАТЬ ЗАПРЕЩЕНО.
"""

METRICS_SYSTEM_PROMPT = """
Ты — эмпатичный ИИ-психолог и аналитик. 
Твоя задача — проанализировать текст дневника пользователя за день и оценить его состояние по 4 метрикам по шкале от 1 до 5 (где 1 - ужасно/очень мало, 5 - отлично/очень много).

ВЫДАЙ ОТВЕТ СТРОГО В ФОРМАТЕ JSON.
Никакого текста до или после JSON. Никаких комментариев.
Используй ТОЛЬКО следующие ключи на английском языке (категорически запрещено их переводить или менять!):

{
  "mood": <целое число 1-5, оценка общего настроения>,
  "energy": <целое число 1-5, уровень энергии и физических сил>,
  "stress": <целое число 1-5, уровень напряжения и стресса (где 5 - очень сильный стресс)>,
  "productivity": <целое число 1-5, продуктивность и закрытие задач>,
  "summary": "<строка, краткое теплое саммари дня на русском языке (1-2 предложения). Обращайся к пользователю на 'ты'>"
}

Если какую-то метрику сложно оценить напрямую, сделай логичный вывод из контекста или ставь 3.
"""

DIGEST_SYSTEM_PROMPT = """
Ты — эмпатичный и аналитический ИИ-ассистент личного дневника DayLog AI.
Твоя задача — проанализировать логи пользователя за неделю (текстовые записи и оценки состояния) и составить структурированный, теплый и полезный еженедельный дайджест.

Правила:
1. Тон: Поддерживающий, как у близкого друга. Обращайся на "ты", не поучай.
2. Анализ: НЕ пытайся высчитывать точные средние баллы. Просто проанализируй общую динамику метрик и текста (например: "неделя началась бодро, но к среде стресс подскочил из-за работы").
3. Краткость: Пиши емко, без воды. Дайджест должен читаться за 1 минуту.

СТРУКТУРА ОТВЕТА (используй Markdown):

🌅 **Главное за неделю:**
[Краткая выжимка основных событий из записей. Без дословного пересказа каждого дня.]

📊 **Твое состояние:**
[Краткий качественный анализ: как менялось настроение, уровень стресса, энергии и продуктивности. Отметь, если есть очевидные закономерности между событиями и состоянием.]

💡 **Мысль недели:**
[Один мягкий инсайт, вывод или поддерживающий совет на следующую неделю.]
"""

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

async def get_ai_question(user_text: str) -> str | None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=messages,
                temperature=0.6,
                timeout=35.0
            )
            return response.choices[0].message.content
        
        except openai.RateLimitError:
            print(f"⚠️ [{PRIMARY_MODEL}] Ошибка 429 (RateLimitError). Жду {2 ** attempt} секунд")
            await asyncio.sleep(2 ** attempt)
            
        except Exception as e:
            print(f"Критическая ошибка ИИ: {e}")
            await asyncio.sleep(2 ** attempt)
            continue

    print(f"⚠️ Модель {PRIMARY_MODEL} перегружена. Врубаем запасную!")
        
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                    model=BACKUP_MODEL,
                    messages=messages,
                    temperature=0.6,
                    timeout=35.0
                )
            return response.choices[0].message.content
        
        except openai.RateLimitError:
            print(f"⚠️ [{BACKUP_MODEL}] Ошибка 429 (RateLimitError). Жду {2 ** attempt} секунд")
            await asyncio.sleep(2 ** attempt)
        
        except Exception as e:
            print(f"Критическая ошибка ИИ: {e}")
            await asyncio.sleep(2 ** attempt)
            continue
    
    print(f"⚠️ Запасная модель {BACKUP_MODEL} тоже легла")
    return None
        
async def get_ai_metrics(user_text: str):
    messages = [
        {"role": "system", "content": METRICS_SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    for attempt in range(3):
        try:
            try:
                response = await client.chat.completions.create(
                    model=PRIMARY_MODEL,
                    messages=messages,
                    temperature=0.1,
                    timeout=90.0,
                    response_format={"type": "json_object"}
                )
                
                raw_text = response.choices[0].message.content
                metrics_dict = json.loads(raw_text)
                return metrics_dict
            
            except openai.RateLimitError:
                print(f"[METRICS] ⚠️ Модель {PRIMARY_MODEL} перегружена. Врубаем запасную!")
                
                response = await client.chat.completions.create(
                    model=BACKUP_MODEL,
                    messages=messages,
                    temperature=0.1,
                    timeout=90.0,
                    response_format={"type": "json_object"}
                )
                
                raw_text = response.choices[0].message.content
                metrics_dict = json.loads(raw_text)
                return metrics_dict
        
        except json.JSONDecodeError:
            print(f"⚠️ Ошибка кривого формата JSON. Жду {2 ** attempt} секунд")
            await asyncio.sleep(2 ** attempt)
        
        except Exception as e:
            # Ловим вообще все остальные критические баги
            print(f"[METRICS] Ошибка: {e}")
            return None
    
    print("[METRICS] ⚠️ Не удалось получить метрики за 3 попытки")
    return None

async def generate_weekly_digest(entries: list) -> str | None:
    compiled_text = "Логи пользователя за неделю:\n\n"
    
    for entry in entries:
        date_str = entry.created_at.strftime("%d.%m.%Y")
        metrics = json.loads(entry.ai_metrics)
        compiled_text += f"Дата: {date_str}\nОценки: Настроение - {metrics['mood']}, Энергия - {metrics['energy']}, Стресс - {metrics['stress']}, Продуктивность - {metrics['productivity']}\nТекст: {entry.user_text}\n\n"
    
    messages = [
        {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
        {"role": "user", "content": compiled_text}
    ]
    
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=messages,
                temperature=0.3,
                timeout=90
            )
            return response.choices[0].message.content
        
        except openai.RateLimitError:
            print(f"⚠️ [{PRIMARY_MODEL}] Ошибка 429 (RateLimitError). Жду {2 ** attempt} секунд")
            await asyncio.sleep(2 ** attempt)
            
        except Exception as e:
            print(f"Критическая ошибка ИИ: {e}")
            await asyncio.sleep(2 ** attempt)
            continue

    print(f"⚠️ Модель {PRIMARY_MODEL} перегружена. Врубаем запасную!")
        
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                    model=BACKUP_MODEL,
                    messages=messages,
                    temperature=0.3,
                    timeout=90
                )
            return response.choices[0].message.content
        
        except openai.RateLimitError:
            print(f"⚠️ [{BACKUP_MODEL}] Ошибка 429 (RateLimitError). Жду {2 ** attempt} секунд")
            await asyncio.sleep(2 ** attempt)
        
        except Exception as e:
            print(f"Критическая ошибка ИИ: {e}")
            await asyncio.sleep(2 ** attempt)
            continue
    
    print(f"⚠️ Запасная модель {BACKUP_MODEL} тоже легла")
    return None