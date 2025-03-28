import telebot
from telebot import types
import psycopg2

# Замените на свои данные
BOT_TOKEN = "8174996234:AAFtcTf8xP9BLNiuQ_QnWpfvQMH9TfTsdZQ"
DB_HOST = "localhost"
DB_NAME = "my_bot_db"
DB_USER = "postgres"
DB_PASSWORD = "1223KarlKarlDomaDoma1223."

bot = telebot.TeleBot(BOT_TOKEN)

# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Функция для получения данных пользователя из базы данных
def get_user_data(user_id):
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor()
        cur.execute("SELECT pinned_site_url, pinned_site_text FROM users WHERE user_id = %s", (user_id,))
        user_data = cur.fetchone()
        if user_data is None:
            # Если пользователя нет в базе, создаем его
            cur.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
            conn.commit()
            return ('https://www.ironfx.com/ru/ironfx-trading-school/financial-news/', 'ironfx.com')  # Значения по умолчанию
        return user_data
    except Exception as e:
        print(f"Ошибка получения данных пользователя: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Функция для обновления закрепленного сайта пользователя в базе данных
def update_pinned_site(user_id, url, text):
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()
        print(f"Updating DB: URL: {url}, Text: {text}, User ID: {user_id}")  # Добавлено логирование
        cur.execute("UPDATE users SET pinned_site_url = %s, pinned_site_text = %s WHERE user_id = %s", (url, text, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка обновления закрепленного сайта: {e}")
        return False
    finally:
        cur.close()
        conn.close()

@bot.message_handler(commands=["start"])
def start(message):
    # Отправляем стартовое сообщение и клавиатуру
    send_start_message(message)

def send_start_message(message):
    user_id = message.from_user.id
    print(f"User ID: {user_id}")
    user_data = get_user_data(user_id)

    if user_data is None:
        bot.send_message(message.chat.id, "Ошибка при получении данных пользователя.")
        return

    pinned_site_url, pinned_site_text = user_data

    markupp = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(
        text=f"Перейти на {pinned_site_text}",
        url=pinned_site_url
    )
    button_2 = types.InlineKeyboardButton(
        text="Новости",
        callback_data="news"
    )
    button_3 = types.InlineKeyboardButton(
        text="Другие сайты",
        callback_data="othersites_menu"
    )
    button_4 = types.InlineKeyboardButton(
        text="Изменить закрепленный сайт",
        callback_data="change_pinned_site"
    )
    markupp.add(button_1)
    markupp.add(button_2)
    markupp.add(button_3)
    markupp.add(button_4)

    message_text = (
        f"Привет, {message.from_user.first_name} {message.from_user.last_name}!\n"
        "Этот бот будет держать тебя в курсе свежих новостей о трейдинге и инвестициях.\n\n"
        "**Список команд:**\n"
        "/information - Информация о боте.\n"
        "/site - Перейти на закреплённый в избранном сайт пользователя.\n"
        "/othersites - Другие сайты с информацией.\n"
        "/news - Получить последние новости.\n"
    )
    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode="Markdown",
        reply_markup=markupp,
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    print(f"Callback {call.data}")
    if call.data == "news":
        bot.send_message(call.message.chat.id, "Здесь будут свежие новости.")
    elif call.data == "othersites_menu":
        # Создаем клавиатуру с сайтами и кнопкой "На главную"
        othersites_markup = types.InlineKeyboardMarkup()
        site1_button = types.InlineKeyboardButton(text="bloomberg.com", callback_data=f"pin|https://www.bloomberg.com/|bloomberg.com")
        site2_button = types.InlineKeyboardButton(text="invest.startengine.com", callback_data=f"pin|https://invest.startengine.com/|startengine.com")
        site3_button = types.InlineKeyboardButton(text="investfunds.ru", callback_data=f"pin|https://investfunds.ru/|investfunds.ru")
        site4_button = types.InlineKeyboardButton(text="tradingview.com", callback_data=f"pin|https://ru.tradingview.com/|tradingview.com")
        main_menu_button = types.InlineKeyboardButton(text="На главную", callback_data="main_menu")  # Кнопка "На главную"

        othersites_markup.add(site1_button)
        othersites_markup.add(site2_button)
        othersites_markup.add(site3_button)
        othersites_markup.add(site4_button)
        othersites_markup.add(main_menu_button)

        bot.send_message(call.message.chat.id, "Выберите сайт для закрепления:", reply_markup=othersites_markup)
    elif call.data == "main_menu":
        # Возвращаемся к стартовому меню
        send_start_message(call.message)
    elif call.data.startswith("pin|"):  # Обработка выбора сайта для закрепления
        # Разбираем callback_data
        parts = call.data.split("|", maxsplit=2)
        if len(parts) == 3:
            _, url, text = parts
            print(f"URL: {url}, Text: {text}")
            # Обновляем URL закрепленного сайта в базе данных
            if update_pinned_site(user_id, url, text):
                # Отправляем подтверждение и возвращаемся в главное меню
                bot.send_message(call.message.chat.id, f"Закрепленный сайт изменен на {text}.")
                send_start_message(call.message)
            else:
                bot.send_message(call.message.chat.id, "Ошибка при обновлении закрепленного сайта.")
        else:
            print(f"Invalid callback {call.data}") # Добавлена информация об ошибке в логи
            bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.") # Сообщение пользователю об ошибке
    elif call.data == "change_pinned_site":
        # Отправляем меню выбора сайта для закрепления
        othersites_markup = types.InlineKeyboardMarkup()
        site1_button = types.InlineKeyboardButton(text="bloomberg.com", callback_data=f"pin|https://www.bloomberg.com/|bloomberg.com")
        site2_button = types.InlineKeyboardButton(text="invest.startengine.com", callback_data=f"pin|https://invest.startengine.com/|startengine.com")
        site3_button = types.InlineKeyboardButton(text="investfunds.ru", callback_data=f"pin|https://investfunds.ru/|investfunds.ru")
        site4_button = types.InlineKeyboardButton(text="tradingview.com", callback_data=f"pin|https://ru.tradingview.com/|tradingview.com")
        main_menu_button = types.InlineKeyboardButton(text="На главную", callback_data="main_menu")  # Кнопка "На главную"

        othersites_markup.add(site1_button)
        othersites_markup.add(site2_button)
        othersites_markup.add(site3_button)
        othersites_markup.add(site4_button)
        othersites_markup.add(main_menu_button)

        bot.send_message(call.message.chat.id, "Выберите сайт для закрепления:", reply_markup=othersites_markup)

@bot.message_handler(commands=["site"])
def site(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    if user_data:
        pinned_site_url, _ = user_data
        bot.send_message(
            message.chat.id,
            pinned_site_url,
        )
    else:
        bot.send_message(message.chat.id, "Ошибка при получении данных пользователя.")

@bot.message_handler(commands=["information"])
def information(message):
    bot.send_message(message.chat.id, "Новости о рынке трейдеров и инвестиций.")

@bot.message_handler(commands=["othersites"])
def othersites(message):
    # Создаем клавиатуру с сайтами и кнопкой "На главную"
    othersites_markup = types.InlineKeyboardMarkup()
    site1_button = types.InlineKeyboardButton(text="bloomberg.com", callback_data=f"pin|https://www.bloomberg.com/|bloomberg.com")
    site2_button = types.InlineKeyboardButton(text="invest.startengine.com", callback_data=f"pin|https://invest.startengine.com/|startengine.com")
    site3_button = types.InlineKeyboardButton(text="investfunds.ru", callback_data=f"pin|https://investfunds.ru/|investfunds.ru")
    site4_button = types.InlineKeyboardButton(text="tradingview.com", callback_data=f"pin|https://ru.tradingview.com/|tradingview.com")
    main_menu_button = types.InlineKeyboardButton(text="На главную", callback_data="main_menu")  # Кнопка "На главную"

    othersites_markup.add(site1_button)
    othersites_markup.add(site2_button)
    othersites_markup.add(site3_button)
    othersites_markup.add(site4_button)
    othersites_markup.add(main_menu_button)

    bot.send_message(message.chat.id, "Выберите сайт:", reply_markup=othersites_markup)

@bot.message_handler(commands=["news"])
def news(message):
    bot.send_message(message.chat.id, "Здесь будут свежие новости")

bot.infinity_polling()