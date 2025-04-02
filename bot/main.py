import logging
from pathlib import Path
from telebot import TeleBot, types
from bot.config import config
from bot.parsers import get_ratings_ru_news
from bot.keyboards import start_keyboard
from bot.database import get_latest_news  # Импортируем новую функцию

# --- Настройка логгирования ---
try:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/bot.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
except Exception as e:
    print(f"Ошибка при инициализации логгера: {e}")
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Не удалось настроить логирование в файл: {e}")

# --- Инициализация бота ---
bot = TeleBot(config.BOT_TOKEN)

def format_news_for_telegram(news_items: list) -> str:
    """Форматирует новости из БД для вывода в Telegram"""
    formatted = []
    for item in news_items:
        domain = item['source'].replace("www.", "")
        formatted.append(f"[{item['title']}]({item['url']}) ({domain})")
    return "\n\n".join(formatted)

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    """Обработчик команды /start."""
    try:
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Привет, {message.from_user.first_name}! Я бот для финансовых новостей.",
            reply_markup=start_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "news_menu")
def handle_news_menu(call: types.CallbackQuery):
    """Обработчик кнопки новостей - сначала проверяет БД, потом парсит при необходимости"""
    try:
        bot.answer_callback_query(call.id, "Загружаю новости...")
        
        # 1. Пытаемся получить новости из БД
        db_news = get_latest_news(limit=10)
        
        if db_news:
            # Если в БД есть новости - показываем их
            formatted_news = format_news_for_telegram(db_news)
            bot.send_message(
                call.message.chat.id,
                "📰 Последние новости из базы данных:\n\n" + formatted_news,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            # Если в БД нет новостей - парсим и сохраняем
            news = get_ratings_ru_news()
            if news:
                bot.send_message(
                    call.message.chat.id,
                    "📰 Последние новости (обновленные):\n\n" + "\n\n".join(news),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                bot.send_message(call.message.chat.id, "⚠️ Не удалось загрузить новости.")
                
    except Exception as e:
        logger.error(f"Ошибка загрузки новостей: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка при загрузке новостей.")

# --- Запуск бота ---
if __name__ == "__main__":
    logger.info("Бот запущен!")
    bot.infinity_polling()