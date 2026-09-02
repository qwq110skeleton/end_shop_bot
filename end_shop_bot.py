import telebot
from telebot import types
import time

# ----------------------------------------
#  НАСТРОЙКИ (замените на свои)
# ----------------------------------------
TOKEN = "8941419428:AAH2Swtq0H0-jDRa3-NGXbdmdOh0Wgks9Ms"  # от @BotFather

# Реквизиты для оплаты в гривнах (перевод на карту)
CARD_NUMBER = "4874 0700 6277 8863"
CARD_OWNER = "End_Shop"

# Криптовалюта (USDT TRC20)
CRYPTO_WALLET = "TLeks35ftpFc3NgGr2AAfzmg3dkCVyHTUz"

# Курс USD/UAH (автоматический пересчёт)
USD_TO_UAH = 45.0

# ID администратора (узнайте у @userinfobot)
ADMIN_ID = 2129276976  # ваш ID

# ----------------------------------------
#  ИНИЦИАЛИЗАЦИЯ
# ----------------------------------------
bot = telebot.TeleBot(TOKEN)

PRODUCTS = {
    "10":  {"name": "10 Random Titan Temples Egg", "price": 0.50, "emoji": "🥚"},
    "25":  {"name": "25 Random Titan Temples Egg", "price": 1.00, "emoji": "🥚"},
    "50":  {"name": "50 Random Titan Temples Egg", "price": 3.00, "emoji": "🥚"},
    "100": {"name": "100 Random Titan Temples Egg", "price": 5.00, "emoji": "🥚"},
    "1000":{"name": "1000 Random Titan Temples Egg", "price": 30.00, "emoji": "🥚"},
    "secret": {"name": "1 Random Secret Egg", "price": 1.00, "emoji": "✨"}
}

carts = {}
first_purchase = {}  # user_id -> bool

def get_cart(user_id):
    return carts.get(user_id, [])

def save_cart(user_id, cart):
    carts[user_id] = cart

def clear_cart(user_id):
    if user_id in carts:
        del carts[user_id]

def get_total(cart):
    return sum(item["price"] for item in cart)

def format_cart(cart, user_id=None):
    if not cart:
        return "🛒 Корзина пуста."
    lines = []
    for item in cart:
        lines.append(f"{item['emoji']} {item['name']} — ${item['price']:.2f}")
    total = get_total(cart)
    if user_id and not first_purchase.get(user_id, False):
        discount_total = total * 0.5
        lines.append(f"\n💰 Итого без скидки: ${total:.2f} (~ {total * USD_TO_UAH:.2f} грн)")
        lines.append(f"🎁 Скидка 50% на первую покупку! Сумма к оплате: ${discount_total:.2f} (~ {discount_total * USD_TO_UAH:.2f} грн)")
    else:
        lines.append(f"\n💰 Итого: ${total:.2f}  (~ {total * USD_TO_UAH:.2f} грн)")
    return "\n".join(lines)

# ----------------------------------------
#  КЛАВИАТУРЫ
# ----------------------------------------
def main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🥚 Steal an Egg", callback_data="steal"),
        types.InlineKeyboardButton("🛒 Корзина", callback_data="cart"),
        types.InlineKeyboardButton("ℹ️ Поддержка", callback_data="support")
    )
    return kb

def categories_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🦖🥚 Titan Temples Eggs", callback_data="category_titan"),
        types.InlineKeyboardButton("🌍 Любая локация", callback_data="category_location"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def products_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🥚 10 яиц - $0.50", callback_data="buy_10"),
        types.InlineKeyboardButton("🥚 25 яиц - $1.00", callback_data="buy_25"),
        types.InlineKeyboardButton("🥚 50 яиц - $3.00", callback_data="buy_50"),
        types.InlineKeyboardButton("🥚 100 яиц - $5.00", callback_data="buy_100"),
        types.InlineKeyboardButton("🥚 1000 яиц - $30.00", callback_data="buy_1000"),
        types.InlineKeyboardButton("✨ Secret Egg - $1.00", callback_data="buy_secret"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_categories")
    )
    return kb

def cart_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💳 Оформить заказ", callback_data="checkout"),
        types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def support_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📩 Связаться с поддержкой", callback_data="contact_support"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def payment_choice_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🇺🇦 Гривны (перевод на карту)", callback_data="pay_uah"),
        types.InlineKeyboardButton("₿ Криптовалюта (USDT)", callback_data="pay_crypto"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def info_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📌 Как проходит сделка", callback_data="info_deal"),
        types.InlineKeyboardButton("💳 Как оплатить", callback_data="info_pay"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
    )
    return kb

def get_reply_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🏪 Магазин"),
        types.KeyboardButton("ℹ️ Информация")
    )
    return kb

# ----------------------------------------
#  ОБРАБОТЧИКИ
# ----------------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    text = (
        "🏪 Добро пожаловать в End_Shop!\n\n"
        "Мы предлагаем товары для Roblox.\n"
        "Используйте кнопки ниже, чтобы начать.\n\n"
        "🎁 Ваша первая покупка со скидкой 50%!\n"
        "Просто добавьте товары в корзину и оформите заказ – скидка применится автоматически."
    )
    bot.send_message(user_id, text, reply_markup=main_menu_keyboard())
    bot.send_message(
        user_id,
        "Нажмите «🏪 Магазин» для главного меню или «ℹ️ Информация» для справки.",
        reply_markup=get_reply_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🏪 Магазин")
def open_shop(message):
    start(message)

@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_menu(message):
    user_id = message.from_user.id
    text = "ℹ️ Информация\n\nВыберите интересующий вас раздел:"
    bot.send_message(user_id, text, reply_markup=info_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "back_main":
        bot.edit_message_text(
            "🏪 Главное меню\nВыберите действие:",
            user_id, call.message.message_id,
            reply_markup=main_menu_keyboard()
        )
        return

    if data == "back_categories":
        bot.edit_message_text(
            "🥚 Выберите категорию:",
            user_id, call.message.message_id,
            reply_markup=categories_keyboard()
        )
        return

    if data == "steal":
        bot.edit_message_text(
            "🥚 Выберите категорию:",
            user_id, call.message.message_id,
            reply_markup=categories_keyboard()
        )
        return

    if data == "category_titan":
        bot.edit_message_text(
            "🦖🥚 Titan Temples Eggs\nВыберите товар:",
            user_id, call.message.message_id,
            reply_markup=products_keyboard()
        )
        return

    if data == "category_location":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_categories"))
        bot.edit_message_text(
            "🌍 Любая локация\n\nК сожалению, товаров в этой категории пока нет.\nОжидайте поступления!",
            user_id, call.message.message_id,
            reply_markup=kb
        )
        return

    if data.startswith("buy_"):
        key = data.split("_")[1]
        product = PRODUCTS.get(key)
        if not product:
            bot.answer_callback_query(call.id, "Товар не найден.")
            return
        cart = get_cart(user_id)
        cart.append({
            "name": product["name"],
            "price": product["price"],
            "emoji": product["emoji"]
        })
        save_cart(user_id, cart)
        bot.answer_callback_query(call.id, f"✅ {product['name']} добавлен в корзину!")
        return

    if data == "cart":
        cart = get_cart(user_id)
        if not cart:
            text = "🛒 Ваша корзина пуста."
        else:
            text = f"🛒 Ваша корзина:\n\n{format_cart(cart, user_id)}"
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=cart_keyboard()
        )
        return

    if data == "clear_cart":
        clear_cart(user_id)
        bot.answer_callback_query(call.id, "🗑️ Корзина очищена.")
        bot.edit_message_text(
            "🛒 Ваша корзина пуста.",
            user_id, call.message.message_id,
            reply_markup=cart_keyboard()
        )
        return

    if data == "checkout":
        cart = get_cart(user_id)
        if not cart:
            bot.answer_callback_query(call.id, "Корзина пуста!")
            return
        total = get_total(cart)
        is_first = not first_purchase.get(user_id, False)
        if is_first:
            discount_total = total * 0.5
            text = (
                f"💳 Оформление заказа\n\n"
                f"Сумма без скидки: ${total:.2f} (~ {total * USD_TO_UAH:.2f} грн)\n"
                f"🎁 Скидка 50% на первую покупку!\n"
                f"Сумма к оплате: ${discount_total:.2f} (~ {discount_total * USD_TO_UAH:.2f} грн)\n\n"
                "Выберите способ оплаты:"
            )
        else:
            text = (
                f"💳 Оформление заказа\n\n"
                f"Сумма: ${total:.2f} (~ {total * USD_TO_UAH:.2f} грн)\n\n"
                "Выберите способ оплаты:"
            )
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=payment_choice_keyboard()
        )
        return

    # ----- ОПЛАТА В ГРИВНАХ -----
    if data == "pay_uah":
        cart = get_cart(user_id)
        if not cart:
            bot.answer_callback_query(call.id, "Корзина пуста!")
            return
        total = get_total(cart)
        is_first = not first_purchase.get(user_id, False)
        if is_first:
            amount_uah = total * 0.5 * USD_TO_UAH
        else:
            amount_uah = total * USD_TO_UAH
        text = (
            f"🇺🇦 Оплата в гривнах\n\n"
            f"Сумма к оплате: {amount_uah:.2f} грн\n\n"
            f"Переведите точную сумму на карту:\n"
            f"{CARD_NUMBER}\n"
            f"Получатель: {CARD_OWNER}\n\n"
            f"После перевода нажмите «✅ Я оплатил»."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Я оплатил", callback_data="uah_paid"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
        )
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=kb
        )
        return

    if data == "uah_paid":
        cart = get_cart(user_id)
        if not cart:
            bot.answer_callback_query(call.id, "Корзина уже пуста.")
            return
        total = get_total(cart)
        is_first = not first_purchase.get(user_id, False)
        if is_first:
            amount_uah = total * 0.5 * USD_TO_UAH
            first_purchase[user_id] = True
        else:
            amount_uah = total * USD_TO_UAH
        admin_text = (
            f"🔔 Новая оплата в гривнах!\n"
            f"Пользователь: @{call.from_user.username or call.from_user.first_name}\n"
            f"ID: {user_id}\n"
            f"Сумма: {amount_uah:.2f} грн\n"
            f"Товары: {', '.join([item['name'] for item in cart])}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass
        clear_cart(user_id)
        bot.answer_callback_query(call.id, "✅ Заказ отправлен на подтверждение!")
        bot.edit_message_text(
            "✅ Ваш заказ принят! Администратор проверит оплату и свяжется с вами.\n\n"
            "⏳ Обычно это занимает до 1 часа.",
            user_id, call.message.message_id,
            reply_markup=main_menu_keyboard()
        )
        return

    # ----- ОПЛАТА В КРИПТОВАЛЮТЕ -----
    if data == "pay_crypto":
        cart = get_cart(user_id)
        if not cart:
            bot.answer_callback_query(call.id, "Корзина пуста!")
            return
        total = get_total(cart)
        is_first = not first_purchase.get(user_id, False)
        if is_first:
            amount_usdt = total * 0.5
        else:
            amount_usdt = total
        text = (
            f"₿ Оплата в криптовалюте\n\n"
            f"Сумма: {amount_usdt:.2f} USDT (TRC20)\n\n"
            f"Переведите точную сумму на адрес:\n"
            f"{CRYPTO_WALLET}\n\n"
            f"После перевода нажмите «✅ Я оплатил»."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Я оплатил", callback_data="crypto_paid"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
        )
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=kb
        )
        return

    if data == "crypto_paid":
        cart = get_cart(user_id)
        if not cart:
            bot.answer_callback_query(call.id, "Корзина уже пуста.")
            return
        total = get_total(cart)
        is_first = not first_purchase.get(user_id, False)
        if is_first:
            amount_usdt = total * 0.5
            first_purchase[user_id] = True
        else:
            amount_usdt = total
        admin_text = (
            f"🔔 Новая оплата криптовалютой!\n"
            f"Пользователь: @{call.from_user.username or call.from_user.first_name}\n"
            f"ID: {user_id}\n"
            f"Сумма: ${amount_usdt:.2f}\n"
            f"Товары: {', '.join([item['name'] for item in cart])}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass
        clear_cart(user_id)
        bot.answer_callback_query(call.id, "✅ Заказ отправлен на подтверждение!")
        bot.edit_message_text(
            "✅ Ваш заказ принят! Администратор проверит оплату и свяжется с вами.\n\n"
            "⏳ Обычно это занимает до 1 часа.",
            user_id, call.message.message_id,
            reply_markup=main_menu_keyboard()
        )
        return

    # ----- ИНФОРМАЦИЯ -----
    if data == "info_deal":
        text = (
            "📌 Как проходит сделка\n\n"
            "1. Вы оформляете заказ и выбираете способ оплаты.\n"
            "2. Оплачиваете точную сумму (карта или криптовалюта).\n"
            "3. Нажимаете «✅ Я оплатил» – мы получаем уведомление.\n"
            "4. В течение 1 часа с вами свяжется наш модератор в личных сообщениях.\n"
            "5. Модератор обсудит все детали и передаст товар.\n\n"
            "Если у вас остались вопросы – напишите в поддержку (кнопка «Поддержка» в главном меню)."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=kb
        )
        return

    if data == "info_pay":
        text = (
            "💳 Как оплатить\n\n"
            "🇺🇦 Оплата картой (гривны):\n"
            "• Переведите точную сумму, указанную ботом, на карту:\n"
            f"  {CARD_NUMBER}\n"
            "  Получатель: End_Shop\n"
            "• После перевода нажмите кнопку «✅ Я оплатил».\n\n"
            "₿ Оплата криптовалютой (USDT TRC20):\n"
            "• Переведите точную сумму USDT на адрес:\n"
            f"  {CRYPTO_WALLET}\n"
            "• Убедитесь, что выбрана сеть TRC20.\n"
            "• После перевода нажмите кнопку «✅ Я оплатил».\n\n"
            "⚠️ Внимание! Переводите ТОЧНО указанную сумму. При несовпадении сумма будет возвращена (за вычетом комиссии)."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=kb
        )
        return

    # ----- ПОДДЕРЖКА -----
    if data == "support":
        text = (
            "ℹ️ Поддержка End_Shop\n\n"
            "🕐 Работаем ежедневно: 8:00 — 23:00\n\n"
            "Если у вас возникли проблемы с заказом — напишите нам."
        )
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=support_keyboard()
        )
        return

    if data == "contact_support":
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📩 Написать в поддержку", url="https://t.me/Ysupport_end_shop"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
        )
        bot.edit_message_text(
            "📩 Связь с поддержкой\n\nНажмите кнопку ниже, чтобы перейти в чат с оператором.",
            user_id, call.message.message_id,
            reply_markup=kb
        )
        return

# ----------------------------------------
#  ЗАПУСК
# ----------------------------------------
if __name__ == "__main__":
    print("Бот End_Shop запущен...")
    bot.polling(none_stop=True)
