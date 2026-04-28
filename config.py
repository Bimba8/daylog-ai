from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    # Указываем, какие переменные мы ЖДЕМ из .env и их типы
    BOT_TOKEN: str
    OPENROUTER_API_KEY: str
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Настройки Pydantic: говорим ему читать файл .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
config = Setting()