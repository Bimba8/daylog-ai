from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db.models import Base # Импортируем базовый класс, чтобы алхимия знала о наших таблицах
from config import config

# Connection pool: pool_pre_ping защищает от stale-коннектов,
# pool_recycle=1800 пересоздаёт их до таймаута PostgreSQL.
# SQL-логирование управляется через DB_ECHO в .env.
engine = create_async_engine(
    config.DATABASE_URL, 
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

# Функция, которая физически создаст таблицы по нашим "чертежам"
# async def init_db():                                             !!! СЕЙЧАС НЕ АКТУАЛЬНО, ВНЕДРИЛИ ALEMBIC !!!
#     # Мы асинхронно подключаемся к базе (engine.begin())
#     # Когда код внутри блока закончится, async with сам разорвет соединение.
#     async with engine.begin() as conn:
#         # Берем метаданные из Base и просим базу создать все таблицы
#         await conn.run_sync(Base.metadata.create_all)