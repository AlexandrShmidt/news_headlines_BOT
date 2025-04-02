from typing import Union, Tuple, List, Dict
from sqlalchemy import Boolean
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from bot.config import config  # Импортируем настройки из config.py
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Подключение к базе данных
engine = create_engine(config.DATABASE_URL)

# 2. Базовый класс для моделей
Base = declarative_base()

# 3. Модель пользователя
class User(Base):
    """
    Таблица users в БД:
    - user_id: ID пользователя Telegram (первичный ключ)
    - pinned_site_url: Закрепленный URL
    - pinned_site_text: Название сайта (для отображения)
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    pinned_site_url = Column(String, nullable=False)
    pinned_site_text = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, site='{self.pinned_site_text}')>"

# 4. Модель новости
class News(Base):
    """
    Таблица news в БД:
    - id: автоинкрементный ID
    - title: заголовок новости
    - url: ссылка на новость
    - source: источник (например, "ironfx.com")
    - published_at: дата публикации (по умолчанию текущая)
    """
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<News(title='{self.title[:20]}...', source='{self.source}')>"
    
class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)  # Уникальный ID пользователя Telegram
    is_active = Column(Boolean, default=True)
    categories = Column(String, default='финансы')  # Категории через запятую
    last_sent_at = Column(DateTime)  # Время последней рассылки

# 5. Создаем таблицы (если их нет)
Base.metadata.create_all(engine)

# 6. Создаем фабрику сессий
Session = sessionmaker(bind=engine)

# 7. Функции для работы с пользователями (оставляем как было)
def get_user_data(user_id: int) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Получает данные пользователя из БД."""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            new_user = User(
                user_id=user_id,
                pinned_site_url="https://www.ironfx.com/ru/ironfx-trading-school/financial-news/",
                pinned_site_text="ironfx.com"
            )
            session.add(new_user)
            session.commit()
            logger.info(f"Создан новый пользователь: {user_id}")
            return new_user.pinned_site_url, new_user.pinned_site_text
            
        return user.pinned_site_url, user.pinned_site_text
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при get_user_data: {e}")
        return None, None
    finally:
        session.close()

# 8. Новые функции для работы с новостями
def save_news(news_items: List[Dict[str, str]]) -> bool:
    """Сохраняет новости в БД (игнорирует дубликаты)."""
    session = Session()
    try:
        for item in news_items:
            # Проверяем, есть ли уже такая новость (по заголовку и источнику)
            exists = session.query(News).filter(
                News.title == item["title"],
                News.source == item["source"]
            ).first()
            
            if not exists:
                news = News(
                    title=item["title"],
                    url=item["url"],
                    source=item["source"]
                )
                session.add(news)
        
        session.commit()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при save_news: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_latest_news(limit: int = 10) -> List[Dict[str, str]]:
    """Получает последние новости из БД."""
    session = Session()
    try:
        news = session.query(News).order_by(News.published_at.desc()).limit(limit).all()
        return [
            {"title": item.title, "url": item.url, "source": item.source}
            for item in news
        ]
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при get_latest_news: {e}")
        return []
    finally:
        session.close()
