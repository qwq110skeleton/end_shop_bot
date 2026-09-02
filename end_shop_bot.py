import telebot
from telebot import types

TOKEN = "8941419428:AAFfc5u8Ye3kX7IHRluzc3FR2BK2myk4ysE"  # обязательно замените!

bot = telebot.TeleBot(TOKEN)

PRODUCTS = {
    "15": {"name": "15 Titan Temples Egg", "price": 1.00, "emoji": "🥚"},
    "40": {"name": "40 Titan Temples Egg", "price": 1.80, "emoji": "🥚"}
}

carts = {}

def get_cart(user_id):
    return carts.get(user_id, [])

def save_cart(user_id, cart):
    carts[user_id] = cart

def clear_cart(user_id):
    if user_id in carts:
        del carts[user_id]

def get_total(cart):
    return sum(item["price"] for item in cart)

def format_cart(cart):
    if not cart:
        return "🛒 Корзина пуста."
    lines = []
    for item in cart:
        lines.append(f"{item['emoji']} {item['name']} — ${item['price']:.2f}")
    total = get_total(cart)
    lines.append(f"\n💰 Итого: ${total:.2f}")
    return "\n".join(lines)

def main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🥚 Steal an Egg", callback_data="steal"),
        types.InlineKeyboardButton("🛒 Корзина", callback_data="cart"),
        types.InlineKeyboardButton("ℹ️ Поддержка", callback_data="support")
    )
    return kb

def products_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🥚 15 яиц - $1.00", callback_data="buy_15"),
        types.InlineKeyboardButton("🥚 40 яиц - $1.80", callback_data="buy_40"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main")
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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    text = (
        "🏪 Добро пожаловать в End_Shop!\n\n"
        "Мы предлагаем товары для Roblox.\n"
        "Используйте кнопки ниже, чтобы начать."
    )
    bot.send_message(user_id, text, reply_markup=main_menu_keyboard())

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

    if data == "steal":
        text = (
            "🥚 Выберите товар:\n\n"
            "• 15 Titan Temples Egg — $1.00\n"
            "• 40 Titan Temples Egg — $1.80\n\n"
            "Нажмите «Купить» под нужным товаром."
        )
        bot.edit_message_text(
            text, user_id, call.message.message_id,
            reply_markup=products_keyboard()
        )
        return

    if data.startswith("buy_"):
        product_key = data.split("_")[1]
        product = PRODUCTS.get(product_key)
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
            text = f"🛒 Ваша корзина:\n\n{format_cart(cart)}"
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
        bot.answer_callback_query(call.id, f"✅ Заказ оформлен! Сумма: ${total:.2f}. Спасибо!")
        clear_cart(user_id)
        bot.edit_message_text(
            "✅ Заказ успешно оформлен!\nСпасибо, что выбрали End_Shop.",
            user_id, call.message.message_id,
            reply_markup=main_menu_keyboard()
        )
        return

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
        # 🔥 Новая логика: показываем кнопку с прямой ссылкой на чат
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

#if __name__ == "__main__":
    #print("Бот End_Shop запущен...")
    #bot.polling(none_stop=True)