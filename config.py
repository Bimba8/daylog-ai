from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    # Указываем, какие переменные мы ЖДЕМ из .env и их типы
    BOT_TOKEN: str
    JWT_SECRET: str
    WEBAPP_URL: str = ""
    ADMIN_IDS: str = ""  # Comma-separated Telegram IDs for admin commands
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    DATABASE_URL: str
    DB_ECHO: bool = False
    REDIS_URL: str
    REDIS_PASSWORD: str
    LOG_LEVEL: str = "INFO"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SENTRY_DSN: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str
    
    # Настройки Pydantic: говорим ему читать файл .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
config = Setting()