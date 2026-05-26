from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db.models import Base # Импортируем базовый класс, чтобы алхимия знала о наших таблицах
from config import config

# FIX: ARCH-04 — Явная настройка connection pool.
# pool_size: количество постоянных соединений в пуле (по умолчанию было 5 — мало).
# max_overflow: доп. соединения сверх pool_size при пиковой нагрузке.
# pool_recycle: пересоздание соединения каждые 1800с, чтобы PostgreSQL не убил stale-коннект.
# pool_pre_ping: проверка «жив ли коннект» перед использованием (SELECT 1).
# echo отключен — SQL-логи управляются через InterceptHandler в logging_config.py,
# который перехватывает sqlalchemy.engine logger и выводит в cyan-формат.
# Уровень SQL-логирования контролируется через DB_ECHO в .env.
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
async def init_db():
    # Мы асинхронно подключаемся к базе (engine.begin())
    # Когда код внутри блока закончится, async with сам разорвет соединение.
    async with engine.begin() as conn:
        # Берем метаданные из Base и просим базу создать все таблицы
        await conn.run_sync(Base.metadata.create_all)