import logging
from pathlib import Path
from telebot import TeleBot, types
from telebot.types import BotCommand
from bot.config import config
from bot.parsers import get_ratings_ru_news
from bot.keyboards import start_keyboard
from bot.database import (
    get_latest_news,
    Session,
    Subscription,
)
from bot.scheduler import start_scheduler

# --- Настройка логгирования ---
def setup_logger():
    try:
        # Создаем папку для логов
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Полный путь к файлу логов
        log_file = log_dir / "bot.log"
        print(f"Логи будут записываться в: {log_file.absolute()}")  # Для диагностики
        
        # Конфигурация логгера
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # Вывод в консоль
            ],
            force=True  # Перезаписать существующие обработчики
        )
        
        logger = logging.getLogger(__name__)
        logger.info("=== Логгер инициализирован ===")
        return logger
        
    except Exception as e:
        print(f"ОШИБКА НАСТРОЙКИ ЛОГГЕРА: {e}")
        raise

# Инициализируем логгер
logger = setup_logger()

# --- Инициализация бота ---
bot = TeleBot(config.BOT_TOKEN)
start_scheduler(bot)

def format_news_for_telegram(news_items: list) -> str:
    """Форматирует новости из БД для вывода в Telegram"""
    formatted = []
    for item in news_items:
        domain = item['source'].replace("www.", "")
        formatted.append(f"[{item['title']}]({item['url']}) ({domain})")
    return "\n\n".join(formatted)

# --- Установка команд бота в боковом меню ---
def setup_bot_commands():
    """Устанавливает команды бота, которые будут отображаться в боковом меню"""
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("news", "Последние новости"),
        BotCommand("subscribe", "Подписаться на рассылку"),
        BotCommand("unsubscribe", "Отписаться от рассылки"),
        BotCommand("help", "Помощь по боту"),
    ]
    bot.set_my_commands(commands)

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    """Обработчик команды /start."""
    try:
        user_name = message.from_user.first_name
        welcome_text = f"""
Привет, {user_name}!
Я бот для финансовых новостей.

📌 Вот список доступных команд:

/news - Получить свежие новости
/subscribe - Подписаться на рассылку
/unsubscribe - Отписаться от рассылки
/help - Помощь по боту

Выберите нужную команду или воспользуйтесь кнопками ниже.
        """
        
        bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            reply_markup=start_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        bot.send_message(
            chat_id=message.chat.id,
            text="⚠️ Произошла ошибка при обработке команды.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['help'])
def handle_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
📌 *Доступные команды:*
/start - Запустить бота
/news - Получить свежие новости
/subscribe - Подписаться на рассылку
/unsubscribe - Отписаться от рассылки
/help - Эта справка

ℹ️ Вы также можете использовать кнопки меню.
    """
    bot.send_message(
        chat_id=message.chat.id,
        text=help_text,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['news'])
def handle_news_command(message: types.Message):
    """Обработчик команды /news"""
    try:
        # Пытаемся получить новости из БД
        db_news = get_latest_news(limit=10)
        
        if db_news:
            formatted_news = format_news_for_telegram(db_news)
            bot.send_message(
                message.chat.id,
                "📰 *Последние новости:*\n\n" + formatted_news,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            news = get_ratings_ru_news()
            if news:
                bot.send_message(
                    message.chat.id,
                    "📰 *Последние новости (обновленные):*\n\n" + "\n\n".join(news),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                bot.send_message(message.chat.id, "⚠️ Не удалось загрузить новости.")
                
    except Exception as e:
        logger.error(f"Ошибка загрузки новостей: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при загрузке новостей.")

@bot.callback_query_handler(func=lambda call: call.data == "news_menu")
def handle_news_menu(call: types.CallbackQuery):
    """Обработчик кнопки новостей"""
    handle_news_command(call.message)  # Используем ту же логику, что и для /news
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['subscribe'])
def handle_subscribe(message: types.Message):
    """Обработчик команды /subscribe"""
    with Session() as session:
        sub = session.query(Subscription).filter_by(user_id=message.from_user.id).first()
        
        if not sub:
            # Если подписки нет вообще - создаем новую
            new_sub = Subscription(user_id=message.from_user.id, is_active=True)
            session.add(new_sub)
            session.commit()
            bot.reply_to(message, "✅ Вы подписались на рассылку!")
        elif not sub.is_active:
            # Если подписка есть, но неактивна - активируем
            sub.is_active = True
            session.commit()
            bot.reply_to(message, "✅ Вы снова подписались на рассылку!")
        else:
            # Если подписка уже активна
            bot.reply_to(message, "ℹ️ Вы уже подписаны!")

@bot.message_handler(commands=['unsubscribe'])
def handle_unsubscribe(message: types.Message):
    """Обработчик команды /unsubscribe"""
    with Session() as session:
        sub = session.query(Subscription).filter_by(user_id=message.from_user.id).first()
        if sub and sub.is_active:
            sub.is_active = False
            session.commit()
            bot.reply_to(message, "🔕 Вы отписались от рассылки.")
        elif sub and not sub.is_active:
            bot.reply_to(message, "ℹ️ Вы уже отписаны.")
        else:
            bot.reply_to(message, "ℹ️ Вы не были подписаны.")


# --- Запуск бота ---
if __name__ == "__main__":
    setup_bot_commands()  # Настраиваем команды меню
    logger.info("Бот запущен!")
    bot.infinity_polling()