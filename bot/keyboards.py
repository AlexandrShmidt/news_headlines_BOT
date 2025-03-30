from telebot import types
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_keyboard() -> types.InlineKeyboardMarkup:
    """
    Главное меню бота с одной кнопкой "Последние новости"
    
    Возвращает:
        InlineKeyboardMarkup: Клавиатура с 1 кнопкой
    """
    try:
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Единственная кнопка - новости
        btn_news = types.InlineKeyboardButton(
            text="📰 Последние новости",
            callback_data="news_menu"
        )
        
        markup.add(btn_news)
        return markup

    except Exception as e:
        logger.error(f"Ошибка при создании клавиатуры: {e}")
        # Возвращаем пустую клавиатуру в случае ошибки
        return types.InlineKeyboardMarkup()