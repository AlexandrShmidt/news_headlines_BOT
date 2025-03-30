import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Optional
import logging

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

def get_ratings_ru_news() -> Optional[List[str]]:
    """Парсит новости с ratings.ru. Возвращает список строк в формате '[Заголовок](URL)' или None при ошибке."""
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
            domain = get_domain_name(full_url)
            
            news_items.append(f"[{title}]({full_url}) ({domain})")

        return news_items if news_items else None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к ratings.ru: {e}")
        return None