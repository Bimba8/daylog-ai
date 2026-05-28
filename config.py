from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    # Указываем, какие переменные мы ЖДЕМ из .env и их типы
    BOT_TOKEN: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    DATABASE_URL: str
    DB_ECHO: bool = False
    REDIS_URL: str
    LOG_LEVEL: str = "INFO"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Настройки Pydantic: говорим ему читать файл .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
config = Setting()