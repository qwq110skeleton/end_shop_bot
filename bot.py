import asyncio
import html
import logging
import os
import signal
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

ADMIN_ID = int(os.environ["ADMIN_ID"])  # твой Telegram ID (узнать: команда /id)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================= НАСТРОЙКИ БОТОВ =======================
ANDROID_URL = "https://play.google.com/store/apps/details?id=com.phygitals.mobile&pcampaignid=web_share"
IOS_URL = "https://apps.apple.com/us/app/phygitals-rip-tcg-packs/id6760307397"

BOT_CONFIGS = [
    {
        # Бот №1: выбор языка (русский / английский)
        "name": "Бот 1",
        "token_env": "BOT_TOKEN",
        "required": True,
        "langs": ["ru", "en"],
        "android": ANDROID_URL,
        "ios": IOS_URL,
        "promo": "4608f6dbd88e",
    },
    {
        # Бот №2: только английский, без меню.
        # Запускается, только если в Render задана переменная BOT_TOKEN_2.
        # Если у второго бота другой промокод или ссылки, поменяй их здесь.
        "name": "Бот 2",
        "token_env": "BOT_TOKEN_2",
        "required": False,
        "langs": ["en"],
        "android": ANDROID_URL,
        "ios": IOS_URL,
        "promo": "4608f6dbd88e",
    },
]

LANG_NAMES = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

# ----------------------------- ТЕКСТЫ -----------------------------
T = {
    "ru": {
        "task": (
            "<b>Задание на 1 минуту 💸</b>\n\n"
            '<b>1.</b> Скачай приложение:\n'
            '📱 Android 👉 <a href="{android}">ТЫК</a>\n'
            '🍏 iPhone 👉 <a href="{ios}">ТЫК</a>\n\n'
            "<b>2.</b> Введи промокод в разделе <b>REWARDS</b>:\n"
            "➡️ <code>{promo}</code> ⬅️ (нажми, чтобы скопировать)\n\n"
            "<b>3.</b> Ты получишь 1$. На него можно купить бокс, из которого падает кэш. "
            "Сейчас он закончился, скоро появится снова!\n\n"
            "После ввода промокода нажми «Выполнено» 👇"
        ),
        "btn_done": "Выполнено ✅",
        "btn_how": "Как это сделать? ❓",
        "how_cap1": "1️⃣ Открой приложение и внизу нажми вкладку Rewards (значок подарка)",
        "how_cap2": "2️⃣ В блоке «Have a referral code?» вставь промокод и нажми Apply",
        "how_text": (
            "📖 <b>Подробная инструкция</b>\n\n"
            "<b>1.</b> Скачай приложение Phygitals по ссылкам из задания и открой его.\n"
            "<b>2.</b> Создай аккаунт или войди в него.\n"
            "<b>3.</b> Внизу экрана нажми вкладку <b>Rewards</b> (значок подарка), как на первом скриншоте.\n"
            "<b>4.</b> Прокрути страницу вниз до блока <b>«Have a referral code?»</b>.\n"
            "<b>5.</b> Вставь промокод <code>{promo}</code> в поле <b>Enter code</b> "
            "(нажми на код, он скопируется) и нажми <b>Apply</b>, как на втором скриншоте. "
            "Проверь, что в коде нет лишних пробелов.\n"
            "<b>6.</b> Приложение покажет, что тебя пригласили, а на баланс "
            "(вверху справа) придёт 1$.\n"
            "<b>7.</b> Сделай скриншот этого экрана, вернись сюда, нажми "
            "<b>«Выполнено ✅»</b> и отправь скриншот."
        ),
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
            '📱 Android 👉 <a href="{android}">TAP</a>\n'
            '🍏 iPhone 👉 <a href="{ios}">TAP</a>\n\n'
            "<b>2.</b> Enter the promo code in the <b>REWARDS</b> section:\n"
            "➡️ <code>{promo}</code> ⬅️ (tap to copy)\n\n"
            "<b>3.</b> You get $1. You can use it to buy a box that drops cash. "
            "It is sold out right now, but it will be back soon!\n\n"
            "After entering the promo code, press “Done” 👇"
        ),
        "btn_done": "Done ✅",
        "btn_how": "How to do it? ❓",
        "how_cap1": "1️⃣ Open the app and tap the Rewards tab (gift icon) at the bottom",
        "how_cap2": "2️⃣ In the “Have a referral code?” block, paste the code and tap Apply",
        "how_text": (
            "📖 <b>Step-by-step guide</b>\n\n"
            "<b>1.</b> Download the Phygitals app using the links in the task and open it.\n"
            "<b>2.</b> Create an account or sign in.\n"
            "<b>3.</b> Tap the <b>Rewards</b> tab (gift icon) at the bottom, like in the first screenshot.\n"
            "<b>4.</b> Scroll down to the <b>“Have a referral code?”</b> block.\n"
            "<b>5.</b> Paste the promo code <code>{promo}</code> into <b>Enter code</b> "
            "(tap the code to copy it) and tap <b>Apply</b>, like in the second screenshot. "
            "Make sure there are no extra spaces in the code.\n"
            "<b>6.</b> The app will show that you were referred, and $1 will appear on "
            "your balance (top right).\n"
            "<b>7.</b> Take a screenshot of this screen, come back here, press "
            "<b>“Done ✅”</b> and send the screenshot."
        ),
        "send_shot": "Send a screenshot showing the promo code entered and the $1 credited 📸",
        "need_shot": "I need a screenshot (photo). Please send it 📸",
        "need_done": "First complete the task and press the “Done” button 👇",
        "sent": "Your screenshot was sent for review ⏳ Please wait for the reply.",
        "already": "Your request is already being reviewed ⏳",
        "ok": "Verified! ✅",
        "no": "Task not accepted ❌ Make sure you entered the promo code and press the button again.",
    },
}


# --------------------------- ВСПОМОГАТЕЛЬНОЕ ---------------------------
def cfg_of(context):
    return context.bot_data["cfg"]


def get_lang(context):
    return context.user_data.get("lang", cfg_of(context)["langs"][0])


def fmt(text, cfg):
    return text.format(android=cfg["android"], ios=cfg["ios"], promo=cfg["promo"])


def lang_kb(langs):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(LANG_NAMES[c], callback_data=f"lang:{c}")] for c in langs]
    )


def task_kb(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(T[lang]["btn_done"], callback_data=f"done:{lang}")],
            [InlineKeyboardButton(T[lang]["btn_how"], callback_data=f"how:{lang}")],
        ]
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


async def send_task(message, cfg, lang):
    await message.reply_text(
        fmt(T[lang]["task"], cfg),
        parse_mode=ParseMode.HTML,
        reply_markup=task_kb(lang),
        disable_web_page_preview=True,
    )


# ----------------------------- ХЕНДЛЕРЫ ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = cfg_of(context)
    context.user_data["awaiting"] = False
    if len(cfg["langs"]) == 1:  # один язык: сразу показываем задание
        lang = cfg["langs"][0]
        context.user_data["lang"] = lang
        await send_task(update.message, cfg, lang)
    else:
        await update.message.reply_text(
            "Выбери язык / Choose your language 👇",
            reply_markup=lang_kb(cfg["langs"]),
        )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")


async def on_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.split(":")[1]
    context.user_data["lang"] = lang
    context.user_data["awaiting"] = False
    await query.answer()
    await send_task(query.message, cfg_of(context), lang)


async def on_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка «Как это сделать?»: два скриншота и подробная инструкция."""
    query = update.callback_query
    lang = query.data.split(":")[1]
    cfg = cfg_of(context)
    await query.answer()

    for i in (1, 2):
        with open(os.path.join(BASE_DIR, f"how{i}.jpg"), "rb") as f:
            await query.message.reply_photo(f, caption=T[lang][f"how_cap{i}"])

    await query.message.reply_text(
        fmt(T[lang]["how_text"], cfg),
        parse_mode=ParseMode.HTML,
        reply_markup=done_kb(lang),
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
    cfg = cfg_of(context)
    pending = context.bot_data.setdefault("pending", set())

    if user.id in pending:
        await msg.reply_text(T[lang]["already"])
        return

    if not context.user_data.get("awaiting"):
        await msg.reply_text(T[lang]["need_done"], reply_markup=done_kb(lang))
        return

    username = f"@{user.username}" if user.username else "—"
    caption = (
        f"Новая заявка на проверку ({cfg['name']})\n"
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
    elif len(cfg_of(context)["langs"]) == 1:
        await update.message.reply_text("Press /start 👇")
    else:
        await update.message.reply_text("Нажми /start 👇 / Press /start")


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


# ------------------------------ ЗАПУСК ------------------------------
def build_app(token, cfg):
    app = Application.builder().token(token).build()
    app.bot_data["cfg"] = cfg
    langs = "|".join(cfg["langs"])
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(on_lang, pattern=rf"^lang:({langs})$"))
    app.add_handler(CallbackQueryHandler(on_how, pattern=rf"^how:({langs})$"))
    app.add_handler(CallbackQueryHandler(on_done, pattern=rf"^done:({langs})$"))
    app.add_handler(
        CallbackQueryHandler(on_admin_decision, pattern=rf"^(ok|no):\d+:({langs})$")
    )
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, on_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


async def run_bots():
    apps = []
    for cfg in BOT_CONFIGS:
        token = os.environ.get(cfg["token_env"])
        if not token:
            if cfg["required"]:
                raise RuntimeError(f"Не задана переменная {cfg['token_env']}")
            logging.info("%s пропущен: нет переменной %s", cfg["name"], cfg["token_env"])
            continue
        apps.append(build_app(token, cfg))

    for app in apps:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows
            pass

    try:
        await stop.wait()
    finally:
        for app in apps:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()


def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    try:
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
