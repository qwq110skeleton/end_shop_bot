import html
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
# httpx пишет в лог полный URL запроса вместе с токеном бота, поэтому глушим
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.environ["BOT_TOKEN"]  # токен от @BotFather
ADMIN_ID = int(os.environ["ADMIN_ID"])  # твой Telegram ID (узнать: команда /id)

ANDROID_URL = "https://play.google.com/store/apps/details?id=com.phygitals.mobile&pcampaignid=web_share"
IOS_URL = "https://apps.apple.com/us/app/phygitals-rip-tcg-packs/id6760307397"
PROMO = "4608f6dbd88e"

LANGS = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

# ----------------------------- ТЕКСТЫ -----------------------------
T = {
    "ru": {
        "task": (
            "<b>Задание на 1 минуту 💸</b>\n\n"
            "<b>1.</b> Скачай приложение:\n"
            f'📱 Android 👉 <a href="{ANDROID_URL}">ТЫК</a>\n'
            f'🍏 iPhone 👉 <a href="{IOS_URL}">ТЫК</a>\n\n'
            "<b>2.</b> Введи промокод в разделе <b>REWARDS</b>:\n"
            f"➡️ <code>{PROMO}</code> ⬅️ (нажми, чтобы скопировать)\n\n"
            "<b>3.</b> Ты получишь 1$. На него можно купить бокс, из которого падает кэш. "
            "Сейчас он закончился, скоро появится снова!\n\n"
            "После ввода промокода нажми кнопку ниже 👇"
        ),
        "btn_done": "Выполнено ✅",
        "send_shot": "Отправь скриншот, где видно, что промокод введён и 1$ начислен 📸",
        "need_shot": "Мне нужен именно скриншот (фото). Отправь его, пожалуйста 📸",
        "need_done": "Сначала выполни задание и нажми кнопку «Выполнено» 👇",
        "sent": "Скриншот отправлен на проверку ⏳ Ожидай ответа.",
        "already": "Твоя заявка уже на проверке ⏳",
        "ok": "Проверено! ✅",
        "no": "Задание не засчитано ❌ Проверь, что ввёл промокод, и нажми кнопку ещё раз.",
    },
    "en": {
        "task": (
            "<b>1-minute task 💸</b>\n\n"
            "<b>1.</b> Download the app:\n"
            f'📱 Android 👉 <a href="{ANDROID_URL}">TAP</a>\n'
            f'🍏 iPhone 👉 <a href="{IOS_URL}">TAP</a>\n\n'
            "<b>2.</b> Enter the promo code in the <b>REWARDS</b> section:\n"
            f"➡️ <code>{PROMO}</code> ⬅️ (tap to copy)\n\n"
            "<b>3.</b> You get $1. You can use it to buy a box that drops cash. "
            "It is sold out right now, but it will be back soon!\n\n"
            "After entering the promo code, press the button below 👇"
        ),
        "btn_done": "Done ✅",
        "send_shot": "Send a screenshot showing the promo code entered and the $1 credited 📸",
        "need_shot": "I need a screenshot (photo). Please send it 📸",
        "need_done": "First complete the task and press the “Done” button 👇",
        "sent": "Your screenshot was sent for review ⏳ Please wait for the reply.",
        "already": "Your request is already being reviewed ⏳",
        "ok": "Verified! ✅",
        "no": "Task not accepted ❌ Make sure you entered the promo code and press the button again.",
    },
}

DEFAULT_LANG = "ru"


# --------------------------- КЛАВИАТУРЫ ---------------------------
def lang_kb():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(name, callback_data=f"lang:{code}")] for code, name in LANGS.items()]
    )


def done_kb(lang):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(T[lang]["btn_done"], callback_data=f"done:{lang}")]]
    )


def admin_kb(user_id, lang):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Проверено ✅", callback_data=f"ok:{user_id}:{lang}"),
            InlineKeyboardButton("Отклонить ❌", callback_data=f"no:{user_id}:{lang}"),
        ]]
    )


def get_lang(context):
    return context.user_data.get("lang", DEFAULT_LANG)


# ----------------------------- ХЕНДЛЕРЫ ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери язык / Choose your language 👇",
        reply_markup=lang_kb(),
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Твой ID: {update.effective_user.id}")


async def on_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.split(":")[1]
    context.user_data["lang"] = lang
    context.user_data["awaiting"] = False
    await query.answer()
    await query.message.reply_text(
        T[lang]["task"],
        parse_mode=ParseMode.HTML,
        reply_markup=done_kb(lang),
        disable_web_page_preview=True,
    )


async def on_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь нажал «Выполнено» -> просим скриншот."""
    query = update.callback_query
    lang = query.data.split(":")[1]
    context.user_data["lang"] = lang

    if query.from_user.id in context.bot_data.setdefault("pending", set()):
        await query.answer(T[lang]["already"], show_alert=True)
        return

    context.user_data["awaiting"] = True
    await query.answer()
    await query.message.reply_text(T[lang]["send_shot"])


async def on_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь прислал скриншот -> пересылаем админу на проверку."""
    user = update.effective_user
    msg = update.message
    lang = get_lang(context)
    pending = context.bot_data.setdefault("pending", set())

    if user.id in pending:
        await msg.reply_text(T[lang]["already"])
        return

    if not context.user_data.get("awaiting"):
        await msg.reply_text(T[lang]["need_done"], reply_markup=done_kb(lang))
        return

    username = f"@{user.username}" if user.username else "—"
    caption = (
        "Новая заявка на проверку\n"
        f"Имя: {html.escape(user.full_name)}\n"
        f"Username: {html.escape(username)}\n"
        f"ID: {user.id}\n"
        f"Язык: {lang}"
    )
    kb = admin_kb(user.id, lang)

    if msg.photo:
        await context.bot.send_photo(
            ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb
        )
    else:  # скриншот, отправленный как файл
        await context.bot.send_document(
            ADMIN_ID, msg.document.file_id, caption=caption, reply_markup=kb
        )

    pending.add(user.id)
    context.user_data["awaiting"] = False
    await msg.reply_text(T[lang]["sent"])


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если ждём скриншот, а пришёл текст — напоминаем."""
    lang = get_lang(context)
    if context.user_data.get("awaiting"):
        await update.message.reply_text(T[lang]["need_shot"])
    else:
        await update.message.reply_text(
            "Нажми /start 👇 / Press /start"
        )


async def on_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ нажал «Проверено» или «Отклонить»."""
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Только для админа", show_alert=True)
        return

    action, user_id, lang = query.data.split(":")
    user_id = int(user_id)

    try:
        if action == "ok":
            await context.bot.send_message(user_id, T[lang]["ok"])
            verdict = "✅ Проверено"
        else:
            await context.bot.send_message(
                user_id, T[lang]["no"], reply_markup=done_kb(lang)
            )
            verdict = "❌ Отклонено"
    except Exception:
        await query.answer("Не удалось отправить сообщение пользователю", show_alert=True)
        return

    context.bot_data.setdefault("pending", set()).discard(user_id)
    await query.answer(verdict)
    await query.edit_message_caption(
        caption=f"{query.message.caption}\n\n{verdict}", reply_markup=None
    )


# ------------------ МИНИ-СЕРВЕР ДЛЯ БЕСПЛАТНОГО RENDER ------------------
class PingHandler(BaseHTTPRequestHandler):
    """Отвечает «ok» на любой запрос: нужен Render и внешнему пингеру."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), PingHandler).serve_forever()


def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(on_lang, pattern=r"^lang:(ru|en)$"))
    app.add_handler(CallbackQueryHandler(on_done, pattern=r"^done:(ru|en)$"))
    app.add_handler(
        CallbackQueryHandler(on_admin_decision, pattern=r"^(ok|no):\d+:(ru|en)$")
    )
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, on_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()
