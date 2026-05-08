import json
import logging
import openai
import asyncio
from openai import AsyncOpenAI
from config import config
from bot.services.prompts import SYSTEM_PROMPT, METRICS_SYSTEM_PROMPT, DIGEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

API_KEY = config.OPENROUTER_API_KEY
PRIMARY_MODEL = "z-ai/glm-4.5-air:free"
BACKUP_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"
BASE_URL = "https://openrouter.ai/api/v1"

# Обязательные ключи и допустимые диапазоны для AI-метрик
_METRIC_KEYS = ("mood", "energy", "stress", "productivity")
_METRIC_RANGE = range(1, 6)  # 1..5

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

# FIX: CRIT-06 — Ограничиваем количество одновременных HTTP-запросов к OpenRouter.
# Без этого при наплыве пользователей каждый создавал неограниченное количество
# параллельных запросов, исчерпывая rate limits и баланс на API.
_ai_semaphore = asyncio.Semaphore(10)


async def _call_with_retry(
    messages: list[dict],
    temperature: float = 0.6,
    timeout: float = 30.0,
    max_retries: int = 2,
    overall_deadline: float = 45.0,
    **extra_kwargs
) -> str | None:
    """
    Универсальная функция вызова LLM с retry + fallback на запасную модель.
    FIX: CRIT-06 — Семафор + общий deadline чтобы юзер не ждал 4+ минут.
    Возвращает текст ответа или None, если все попытки провалились.
    """
    # FIX: CRIT-06 — Семафор ограничивает параллелизм, чтобы не завалить API
    async with _ai_semaphore:
        # Общий deadline: если все retry + fallback не уложились в overall_deadline — сдаёмся.
        # Раньше worst-case мог занять 4+ минуты (юзер видел "Анализирую..." всё это время).
        deadline = asyncio.get_event_loop().time() + overall_deadline
        
        for model in (PRIMARY_MODEL, BACKUP_MODEL):
            for attempt in range(max_retries):
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    logger.error("Overall deadline exceeded, aborting AI call")
                    return None
                
                try:
                    # asyncio.wait_for гарантирует, что один запрос не зависнет дольше timeout.
                    # min(timeout, remaining) учитывает остаток общего deadline.
                    response = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            **extra_kwargs
                        ),
                        timeout=min(timeout, remaining)
                    )
                    return response.choices[0].message.content
                
                except asyncio.TimeoutError:
                    logger.warning(f"[{model}] Timeout (попытка {attempt + 1}/{max_retries})")
                
                except openai.RateLimitError:
                    wait = 2 ** attempt
                    logger.warning(f"[{model}] RateLimitError. Жду {wait}с (попытка {attempt + 1}/{max_retries})")
                    # min(wait, remaining) — не ждём дольше, чем осталось до deadline
                    await asyncio.sleep(min(wait, max(0, remaining)))
                
                except Exception as e:
                    wait = 2 ** attempt
                    logger.error(f"[{model}] Ошибка: {e}. Жду {wait}с (попытка {attempt + 1}/{max_retries})")
                    await asyncio.sleep(min(wait, max(0, remaining)))
            
            logger.warning(f"Модель {model} исчерпала {max_retries} попыток, переключаемся...")
        
        logger.error("Все модели недоступны, возвращаем None")
        return None


def _validate_metrics(data: dict) -> dict | None:
    """
    Проверяет, что ответ AI содержит все нужные метрики с корректными значениями.
    Приводит значения к int и зажимает в диапазон 1-5.
    """
    try:
        for key in _METRIC_KEYS:
            val = data.get(key)
            if val is None:
                data[key] = 3  # fallback по умолчанию
            else:
                data[key] = max(1, min(5, int(val)))
        
        if "summary" not in data or not isinstance(data["summary"], str):
            data["summary"] = "Без комментариев."
        
        return data
    except (ValueError, TypeError) as e:
        logger.warning(f"Ошибка валидации метрик: {e}")
        return None


async def get_ai_response(user_text: str) -> str | None:
    """Получить ответ/вопрос AI на текст пользователя (диалог дневника).
    
    FIX: ARCH-02 — Интерактивный запрос (юзер ждёт ответа в чате).
    Жёсткий overall_deadline=35с, чтобы юзер не видел «Анализирую...» дольше полуминуты.
    max_retries=2 — только 2 попытки на модель, потом fallback.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    return await _call_with_retry(
        messages, temperature=0.6, timeout=25.0, max_retries=2, overall_deadline=35.0
    )


async def get_ai_metrics(user_text: str) -> dict | None:
    """Получить AI-метрики настроения/энергии/стресса/продуктивности из текста дневника.
    
    FIX: ARCH-02 — Фоновый запрос (юзер не ждёт напрямую, запущен через asyncio.Task).
    overall_deadline=60с на каждую попытку — щедрее, чем интерактивный,
    но всё равно ограничен, чтобы фоновая задача не висела вечно.
    """
    messages = [
        {"role": "system", "content": METRICS_SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    for attempt in range(3):
        raw_text = await _call_with_retry(
            messages,
            temperature=0.1,
            timeout=40.0,
            max_retries=2,
            overall_deadline=60.0,
            response_format={"type": "json_object"}
        )
        
        if not raw_text:
            return None
        
        try:
            metrics_dict = json.loads(raw_text)
            validated = _validate_metrics(metrics_dict)
            if validated:
                return validated
            logger.warning(f"Метрики не прошли валидацию (попытка {attempt + 1}/3)")
        except json.JSONDecodeError:
            logger.warning(f"Кривой JSON от AI (попытка {attempt + 1}/3)")
            await asyncio.sleep(2 ** attempt)
    
    logger.error("Не удалось получить валидные метрики за все попытки")
    return None


async def generate_weekly_digest(entries: list) -> str | None:
    """Сгенерировать еженедельный AI-дайджест на основе записей."""
    compiled_text = "Логи пользователя за неделю:\n\n"
    
    for entry in entries:
        date_str = entry.created_at.strftime("%d.%m.%Y")
        if not entry.ai_metrics:
            compiled_text += f"Дата: {date_str}\nОценки: нет данных\nТекст: {entry.user_text}\n\n"
            continue
        metrics = json.loads(entry.ai_metrics)
        compiled_text += f"Дата: {date_str}\nОценки: Настроение - {metrics.get('mood', '?')}, Энергия - {metrics.get('energy', '?')}, Стресс - {metrics.get('stress', '?')}, Продуктивность - {metrics.get('productivity', '?')}\nТекст: {entry.user_text}\n\n"
    
    messages = [
        {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
        {"role": "user", "content": compiled_text}
    ]
    
    return await _call_with_retry(messages, temperature=0.3, timeout=90.0)