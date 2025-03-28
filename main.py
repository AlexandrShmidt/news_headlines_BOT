import telebot
from telebot import types

bot = telebot.TeleBot("8174996234:AAFtcTf8xP9BLNiuQ_QnWpfvQMH9TfTsdZQ")  # Замените на свой токен


@bot.message_handler(commands=["start"])
def start(message):
    # Отправляем стартовое сообщение и клавиатуру
    send_start_message(message)


def send_start_message(message):  # Функция для отправки стартового сообщения
    markupp = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(
        text="Перейти на закреплённый сайт",
        url="https://www.ironfx.com/ru/ironfx-trading-school/financial-news/"
    )
    button_2 = types.InlineKeyboardButton(
        text="Новости",
        callback_data="news"
    )
    button_3 = types.InlineKeyboardButton(
        text="Другие сайты",
        callback_data="othersites_menu"
    )
    markupp.add(button_1)
    markupp.add(button_2)
    markupp.add(button_3)

    message_text = (
        f"Привет, {message.from_user.first_name} {message.from_user.last_name}!\n"
        "Этот бот будет держать тебя в курсе свежих новостей о трейдинге и инвестициях.\n\n"
        "**Список команд:**\n"
        "/information - Информация о боте.\n"
        "/site - Закреплённый в избранном сайт пользователя.\n"
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
    if call.data == "news":
        bot.send_message(call.message.chat.id, "Здесь будут свежие новости.")
    elif call.data == "othersites_menu":
        # Создаем клавиатуру с сайтами и кнопкой "На главную"
        othersites_markup = types.InlineKeyboardMarkup()
        site1_button = types.InlineKeyboardButton(text="bloomberg.com", url="https://www.bloomberg.com/")
        site2_button = types.InlineKeyboardButton(text="invest.startengine.com", url="https://invest.startengine.com/")
        site3_button = types.InlineKeyboardButton(text="investfunds.ru", url="https://investfunds.ru/")
        site4_button = types.InlineKeyboardButton(text="tradingview.com", url="https://ru.tradingview.com/")
        main_menu_button = types.InlineKeyboardButton(text="На главную", callback_data="main_menu")  # Кнопка "На главную"

        othersites_markup.add(site1_button)
        othersites_markup.add(site2_button)
        othersites_markup.add(site3_button)
        othersites_markup.add(site4_button)
        othersites_markup.add(main_menu_button)  # Добавляем кнопку "На главную"

        bot.send_message(call.message.chat.id, "Выберите сайт:", reply_markup=othersites_markup)
    elif call.data == "main_menu":
        # Возвращаемся к стартовому меню
        send_start_message(call.message)  # Вызываем функцию отправки стартового сообщения


@bot.message_handler(commands=["site"])
def site(message):
    bot.send_message(
        message.chat.id,
        "https://www.ironfx.com/ru/ironfx-trading-school/financial-news/",
    )


@bot.message_handler(commands=["information"])
def information(message):
    bot.send_message(message.chat.id, "Новости о рынке трейдеров и инвестиций.")

@bot.message_handler(commands=["othersites"])
def othersites(message):
    # Создаем клавиатуру с сайтами и кнопкой "На главную"
    othersites_markup = types.InlineKeyboardMarkup()
    site1_button = types.InlineKeyboardButton(text="bloomberg.com", url="https://www.bloomberg.com/")
    site2_button = types.InlineKeyboardButton(text="invest.startengine.com", url="https://invest.startengine.com/")
    site3_button = types.InlineKeyboardButton(text="investfunds.ru", url="https://investfunds.ru/")
    site4_button = types.InlineKeyboardButton(text="tradingview.com", url="https://ru.tradingview.com/")
    main_menu_button = types.InlineKeyboardButton(text="На главную", callback_data="main_menu")  # Кнопка "На главную"

    othersites_markup.add(site1_button)
    othersites_markup.add(site2_button)
    othersites_markup.add(site3_button)
    othersites_markup.add(site4_button)
    othersites_markup.add(main_menu_button)  # Добавляем кнопку "На главную"

    bot.send_message(message.chat.id, "Выберите сайт:", reply_markup=othersites_markup)


@bot.message_handler(commands=["news"])
def news(message):
    bot.send_message(message.chat.id, "Здесь будут свежие новости")


bot.polling(none_stop=True)