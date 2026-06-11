from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Text, func, ForeignKey, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Это базовый класс, от которого будут наследоваться все наши таблицы. 
# SQLAlchemy использует его, чтобы понимать, какие вообще таблицы есть в проекте.
class Base(DeclarativeBase):
    pass

# заготовка для таблицы пользователей
class User(Base):
    __tablename__ = 'users'
    
    # Mapped[тип] указывает Python, какой это тип данных, 
    # mapped_column() рассказывает SQLAlchemy, как это сохранить в базе.
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    timezone: Mapped[str] = mapped_column(String, default="Europe/Moscow")
    reminder_time: Mapped[str] = mapped_column(String, default="20:00")
    digest_day: Mapped[int] = mapped_column(Integer, default=0)
    digest_time: Mapped[int] = mapped_column(Integer, default=12)
    
    # Связь с записями дневника: user.entries вернет все DiaryEntry этого юзера
    entries: Mapped[list["DiaryEntry"]] = relationship(back_populates="user", lazy="selectin")
    
    
class DiaryEntry(Base):
    __tablename__ = 'diary_entries'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id')) # Вот так мы создаем связь. Мы указываем имя_таблицы.имя_колонки ('users.id') в функции ForeignKey
    user_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ai_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Обратная связь: entry.user вернет объект User
    user: Mapped["User"] = relationship(back_populates="entries")