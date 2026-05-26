import json
import aiohttp
from loguru import logger
from config import config
from tenacity import retry, wait_exponential_jitter, retry_if_exception_type, stop_after_attempt
from bot.services.prompts import SYSTEM_PROMPT, METRICS_SYSTEM_PROMPT, DIGEST_SYSTEM_PROMPT

logger = logger.bind(module="AI")

# Обязательные ключи для AI-метрик
_METRIC_KEYS = ("mood", "energy", "stress", "productivity")

def _validate_metrics(data: dict) -> dict | None:
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
        logger.warning("Ошибка валидации метрик: {}", e)
        return None

class AIRouter:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.groq_api_key = config.GROQ_API_KEY
        self.gemini_api_key = config.GEMINI_API_KEY
        
    async def start(self):
        """Открываем глобальную сессию при старте бота"""
        self.session = aiohttp.ClientSession()
        logger.info("HTTP-сессия открыта")
        
    async def close(self):
        """Закрываем сессию при выключении"""
        if self.session:
            await self.session.close()
            logger.info("HTTP-сессия закрыта")
    
    # Декоратор: ждем от 2 до 10 секунд, максимум 3 попытки, 
    # ловим только ошибки HTTP (например 429 или 500)
    @retry(
        wait=wait_exponential_jitter(initial=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(aiohttp.ClientResponseError),
        reraise=True # Пробросит ошибку наверх, если попытки кончатся
    )
    async def _call_groq(self, model: str, messages: list[dict], is_json: bool = False) -> dict:
        """Приватный метод для стука в Groq"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1 if is_json else 0.6  # Для JSON нужна минимальная температура!
        }
        
        # Если попросили JSON — динамически добавляем ключ в дикт
        if is_json:
            payload["response_format"] = {"type": "json_object"}
        
        # self.session УЖЕ должен быть инициализирован в start()
        async with self.session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status() # Бросает ClientResponseError при 4xx/5xx
            return await response.json()
        
    @retry(
        wait=wait_exponential_jitter(initial=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(aiohttp.ClientResponseError),
        reraise=True # Пробросит ошибку наверх, если попытки кончатся
    )
    async def _call_google(self, model: str, messages: list[dict], is_json: bool = False) -> dict:
        """Приватный метод для стука в Google (Gemini).
        Сам конвертирует стандартные messages в payload Гугла.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        
        # Конвертируем формат: Google ждет role="user" или "model", а контент внутри "parts" [{"text": ...}]
        google_contents = []
        for m in messages:
            # Если это system prompt, Google обычно просит передавать его отдельно (systemInstruction), 
            # но для простоты мы можем притвориться, что это тоже сказал user.
            role = "user" if m["role"] in ("user", "system") else "model"
            google_contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })
    
        payload = {"contents": google_contents}
        headers = {"Content-Type": "application/json"}
        
        if is_json:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status() # Бросит ошибку при 429/500, tenacity перехватит
            return await response.json()
            
            
ai_router = AIRouter()
MAIN_GROQ_MODEL = "llama-3.3-70b-versatile"
SECOND_GROQ_MODEL = "llama-3.1-8b-instant"
GOOGLE_MODEL = "gemini-3.1-flash-lite"

# --- Фасады (интерфейсы для остального кода не меняем!) ---
async def get_ai_response(user_text: str) -> str | None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    try:
        # Уровень 1: Пробуем Groq 70B
        response = await ai_router._call_groq(MAIN_GROQ_MODEL, messages)
        return response['choices'][0]['message']['content']
    
    except Exception as e:
        logger.warning("Groq {} недоступен ({}), фоллбэк → {}", MAIN_GROQ_MODEL, e, SECOND_GROQ_MODEL)
        
        try:
            # Уровень 2: Фоллбэк внутри Groq (8B)
            response = await ai_router._call_groq(SECOND_GROQ_MODEL, messages)
            return response['choices'][0]['message']['content']
        except Exception as e2:
            logger.warning("Groq лёг ({}), кросс-провайдер фоллбэк → {}", e2, GOOGLE_MODEL)
            
            try:
                # Уровень 3: Кросс-провайдерный фоллбэк
                response = await ai_router._call_google(GOOGLE_MODEL, messages)
                # У Гугла другой путь к тексту ответа в JSON:
                return response['candidates'][0]['content']['parts'][0]['text']
            except Exception as e3:
                # Уровень 4: Сдаемся
                logger.error("Все AI-провайдеры лежат: {}", e3)
                return None
        

async def get_ai_metrics(user_text: str) -> dict | None:
    messages = [
        {"role": "system", "content": METRICS_SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]
    
    raw_text = None
    
    try:
        response = await ai_router._call_groq("llama-3.1-8b-instant", messages, is_json=True)
        raw_text = response['choices'][0]['message']['content']
    except Exception as e:
        logger.warning("Groq 8B недоступен для метрик ({}), фоллбэк → Google", e)
        
        try:
            response = await ai_router._call_google("gemini-2.5-flash", messages, is_json=True)
            raw_text = response['candidates'][0]['content']['parts'][0]['text']
        except Exception as e2:
            logger.error("Все провайдеры лежат для метрик: {}", e2)
            return None
        
    if raw_text:
        try:
            metrics_dict = json.loads(raw_text)
            return _validate_metrics(metrics_dict)  # Твоя старая добрая валидация
        except json.JSONDecodeError:
            logger.error("ИИ вернул невалидный JSON: {}", raw_text[:200])
            return None

async def generate_weekly_digest(entries: list) -> str | None:
    """Сгенерировать еженедельный AI-дайджест на основе записей."""
    compiled_text = "Логи пользователя за неделю:\n\n"
    
    for entry in entries:
        date_str = entry.created_at.strftime("%d.%m.%Y")
        if not entry.ai_metrics:
            compiled_text += f"Дата: {date_str}\nОценки: нет данных\nТекст: {entry.user_text}\n\n"
            continue
            
        try:
            metrics = json.loads(entry.ai_metrics)
            compiled_text += f"Дата: {date_str}\nОценки: Настроение - {metrics.get('mood', '?')}, Энергия - {metrics.get('energy', '?')}, Стресс - {metrics.get('stress', '?')}, Продуктивность - {metrics.get('productivity', '?')}\nТекст: {entry.user_text}\n\n"
        except json.JSONDecodeError:
            compiled_text += f"Дата: {date_str}\nОценки: ошибка парсинга\nТекст: {entry.user_text}\n\n"
    
    messages = [
        {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
        {"role": "user", "content": compiled_text}
    ]
    
    try:
        # Для дайджестов идем СРАЗУ в Гугл (нужно большое контекстное окно), без каскада Groq
        response = await ai_router._call_google("gemini-2.5-flash", messages)
        # Парсим ответ по наркоманской структуре Гугла
        return response['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error("Ошибка генерации дайджеста: {}", e)
        return None