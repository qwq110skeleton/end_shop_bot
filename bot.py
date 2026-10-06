import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]   # токен от @BotFather
ADMIN_ID = int(os.environ["ADMIN_ID"])  # твой Telegram ID (узнать: команда /id в этом боте)

TASK_TEXT = (
    "<b>Задание на 1 минуту 💸</b>\n\n"
    "<b>1.</b> Скачай приложение:\n"
    '📱 Android 👉 <a href="https://play.google.com/store/apps/details?id=com.phygitals.mobile&pcampaignid=web_share">ТЫК</a>\n'
    '🍏 iPhone 👉 <a href="https://apps.apple.com/us/app/phygitals-rip-tcg-packs/id6760307397">ТЫК</a>\n\n'
    "<b>2.</b> Введи промокод в разделе <b>REWARDS</b>:\n"
    "➡️ <code>4608f6dbd88e</code> ⬅️ (нажми, чтобы скопировать)\n\n"
    "<b>3.</b> Ты получишь 1$. На него можно купить бокс, из которого падает кэш. "
    "Сейчас он закончился, скоро появится снова!\n\n"
    "После ввода промокода нажми кнопку ниже 👇"
)

DONE_KB = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Выполнено ✅", callback_data="done")]]
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        TASK_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=DONE_KB,
        disable_web_page_preview=True,
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Твой ID: {update.effective_user.id}")


async def on_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь нажал «Выполнено» -> отправляем заявку админу."""
    query = update.callback_query
    user = query.from_user
    pending = context.bot_data.setdefault("pending", set())

    if user.id in pending:
        await query.answer("Заявка уже на проверке ⏳", show_alert=True)
        return

    pending.add(user.id)
    await query.answer()
    await query.message.reply_text("Заявка отправлена на проверку ⏳ Ожидай ответа.")

    name = html.escape(user.full_name)
    username = f"@{html.escape(user.username)}" if user.username else "—"
    admin_kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Проверено ✅", callback_data=f"ok:{user.id}"),
            InlineKeyboardButton("Отклонить ❌", callback_data=f"no:{user.id}"),
        ]]
    )
    await context.bot.send_message(
        ADMIN_ID,
        f"<b>Новая заявка на проверку</b>\n"
        f"Имя: {name}\nUsername: {username}\nID: <code>{user.id}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_kb,
    )


async def on_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ нажал «Проверено» или «Отклонить»."""
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("Только для админа", show_alert=True)
        return

    action, user_id = query.data.split(":")
    user_id = int(user_id)
    context.bot_data.setdefault("pending", set()).discard(user_id)

    if action == "ok":
        await context.bot.send_message(user_id, "Проверено! ✅")
        verdict = "✅ Проверено"
    else:
        await context.bot.send_message(
            user_id,
            "Задание не засчитано ❌ Проверь, что ввёл промокод, и нажми кнопку ещё раз.",
            reply_markup=DONE_KB,
        )
        verdict = "❌ Отклонено"

    await query.answer(verdict)
    await query.edit_message_text(
        f"{query.message.text}\n\n{verdict}", reply_markup=None
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(on_done, pattern=r"^done$"))
    app.add_handler(CallbackQueryHandler(on_admin_decision, pattern=r"^(ok|no):\d+$"))
    app.run_polling()


if __name__ == "__main__":
    main()
