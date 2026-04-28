from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db.models import Base # Импортируем базовый класс, чтобы алхимия знала о наших таблицах
from config import config

engine = create_async_engine(
    config.DATABASE_URL, 
    echo=config.DB_ECHO  # <--- Теперь Алхимия слушает наш конфиг
) # Создаем движок (подключение к SQLite). "sqlite+aiosqlite" означает, что мы используем SQLite в асинхронном режиме. Файл базы будет называться diary.db и появится в корне твоего проекта.

async_session = async_sessionmaker(engine, expire_on_commit=False) # Создаем "фабрику сессий". Бот будет использовать её, чтобы открывать сессию для каждого нового действия.

# Функция, которая физически создаст таблицы по нашим "чертежам"
async def init_db():
    # Мы асинхронно подключаемся к базе (engine.begin())
    # Когда код внутри блока закончится, async with сам разорвет соединение.
    async with engine.begin() as conn:
        # Берем метаданные из Base и просим базу создать все таблицы
        await conn.run_sync(Base.metadata.create_all)