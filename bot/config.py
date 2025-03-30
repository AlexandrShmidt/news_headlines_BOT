import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any

# Загружаем переменные из .env
load_dotenv()

class Settings:
    # 1. Основные настройки бота
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = [123456789]  # ID администраторов (можно добавить несколько)
    
    # 2. Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db_name")
    
    # 3. Настройки парсеров
    PARSERS_CONFIG: Dict[str, Any] = {
        "ratings": {
            "url": "https://ratings.ru/news/",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "timeout": 10
        },
        "investing": {
            "url": "https://ru.investing.com/news/",
            "headers": {"User-Agent": "Mozilla/5.0"},
            "timeout": 10
        }
    }
    
    # 4. Дефолтные значения для пользователей
    DEFAULT_SITE: Dict[str, str] = {
        "url": "https://www.ironfx.com/ru/ironfx-trading-school/financial-news/",
        "text": "ironfx.com"
    }

# Создаем экземпляр настроек
config = Settings()