import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Optional, Dict
import logging
from datetime import datetime
from bot.database import save_news  # Импортируем функцию для сохранения в БД

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_domain_name(url: str) -> str:
    """Извлекает доменное имя из URL (например, 'https://google.com/news' -> 'google.com')"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        return domain.replace("www.", "")  # Убираем 'www.' для краткости
    except Exception as e:
        logger.error(f"Ошибка при разборе URL {url}: {e}")
        return url  # Возвращаем исходный URL как fallback

def parse_ratings_ru_news() -> Optional[List[Dict[str, str]]]:
    """
    Парсит новости с ratings.ru.
    Возвращает список словарей в формате:
    [
        {"title": "...", "url": "...", "source": "ratings.ru"},
        ...
    ]
    или None при ошибке.
    """
    try:
        url = "https://ratings.ru/news/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = []
        
        for item in soup.find_all("div", class_="news-preview__item"):
            title_element = item.find("a", class_="news-preview__title")
            if not title_element:
                continue

            title = title_element.text.strip()
            relative_url = title_element["href"]
            full_url = f"https://ratings.ru{relative_url}"
            
            news_items.append({
                "title": title,
                "url": full_url,
                "source": "ratings.ru"
            })

        return news_items if news_items else None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к ratings.ru: {e}")
        return None

def get_ratings_ru_news() -> Optional[List[str]]:
    """
    Основная функция для получения новостей.
    Парсит и сохраняет в БД, затем возвращает в формате для Telegram.
    """
    news_data = parse_ratings_ru_news()
    if not news_data:
        return None
    
    # Сохраняем новости в БД
    if not save_news(news_data):
        logger.error("Не удалось сохранить новости в БД, но продолжаем работу")
    
    # Форматируем для вывода в Telegram
    formatted_news = []
    for item in news_data:
        domain = get_domain_name(item["url"])
        formatted_news.append(f"[{item['title']}]({item['url']}) ({domain})")
    
    return formatted_news