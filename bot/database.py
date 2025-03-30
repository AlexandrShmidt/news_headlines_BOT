from typing import Union, Tuple
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
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

# 4. Создаем таблицы (если их нет)
Base.metadata.create_all(engine)

# 5. Создаем фабрику сессий
Session = sessionmaker(bind=engine)

# 6. Функции для работы с БД
def get_user_data(user_id: int) -> Union[Tuple[str, str], Tuple[None, None]]:
    """
    Получает данные пользователя из БД.
    Если пользователя нет — создает нового с дефолтными значениями.
    
    Возвращает: (pinned_site_url, pinned_site_text) или (None, None) при ошибке
    """
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            # Создаем нового пользователя
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

def update_pinned_site(user_id: int, url: str, text: str) -> bool:
    """
    Обновляет закрепленный сайт пользователя.
    
    Возвращает: 
    - True при успехе
    - False при ошибке или если пользователь не найден
    """
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            logger.warning(f"Пользователь {user_id} не найден")
            return False
            
        user.pinned_site_url = url
        user.pinned_site_text = text
        session.commit()
        logger.info(f"Обновлен сайт для {user_id}: {text}")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при update_pinned_site: {e}")
        session.rollback()
        return False
    finally:
        session.close()