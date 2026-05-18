import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logger = logging.getLogger(__name__)


# ─── Send message ────────────────────────────────────────────────────────────

async def send_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

def notify(text):
    asyncio.run(send_message(text))


# ─── Send message with button ────────────────────────────────────────────────

async def send_with_button(text, callback_data):
    bot = Bot(token=TELEGRAM_TOKEN)

    button_labels = {
        "confirm_cancel": "Cancelled ✅",
        "confirm_renewal": "Renewed ✅"
    }
    button_text = button_labels.get(callback_data, "Confirm ✅")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=callback_data)]
    ])
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"Message with button '{button_text}' sent to chat {CHAT_ID}.")

def notify_with_button(text, callback_data):
    asyncio.run(send_with_button(text, callback_data))


# ─── Button handler ──────────────────────────────────────────────────────────

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logger.info(f"Button pressed: '{data}'")

    if data == "confirm_cancel":
        from sheets import update_status
        from memory import load_pending, clear_pending, add_awaiting_group

        cancellations = load_pending()
        for c in cancellations:
            update_status(SPREADSHEET_ID, c["tab_name"], c["row_index"], "To be terminated")
            logger.info(f"Status updated to 'To be terminated': {c['name']}")

        add_awaiting_group(cancellations)
        clear_pending()

        await query.answer("✅ Statuses updated!")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Statuses updated. In 2 business days I will ask if Michal confirmed the cancellation."
        )

    elif data == "confirm_renewal":
        from sheets import update_status
        from memory import load_pending, clear_pending

        renewals = load_pending(pending_type="renewal")
        for r in renewals:
            update_status(SPREADSHEET_ID, r["tab_name"], r["row_index"], "Expired")
            logger.info(f"Status updated to 'Expired': {r['name']}")

        clear_pending(pending_type="renewal")

        await query.answer("✅ Statuses updated!")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Statuses updated: *Expired*",
            parse_mode="Markdown"
        )

    elif data.startswith("confirmed:"):
        from sheets import update_status
        from memory import load_awaiting, confirm_group

        group_id = data.split(":")[1]
        groups = load_awaiting()
        for g in groups:
            if g["id"] == group_id:
                for c in g["cancellations"]:
                    update_status(SPREADSHEET_ID, c["tab_name"], c["row_index"], "Terminated")
                    logger.info(f"Status updated to 'Terminated': {c['name']}")
                break

        confirm_group(group_id)
        await query.edit_message_text(
            text="✅ Done! Statuses updated: *Terminated*",
            parse_mode="Markdown"
        )

    elif data.startswith("postpone:"):
        from memory import postpone_group

        group_id = data.split(":")[1]
        postpone_group(group_id)
        logger.info(f"Group '{group_id}' postponed.")

        await query.edit_message_text(
            text="⏳ Got it, I will ask again tomorrow.",
            parse_mode="Markdown"
        )


# ─── Text message handler ─────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from memory import load_pending, save_pending
    from llm import find_exclusions

    user_message = update.message.text
    logger.info(f"Text message received: '{user_message}'")

    cancellations = load_pending(pending_type="cancel")
    if not cancellations:
        await update.message.reply_text("No active cancellations found.")
        return

    exclusions = find_exclusions(user_message, cancellations)
    if not exclusions:
        await update.message.reply_text("Could not understand who to exclude. Try writing a name or number.")
        return

    updated = [c for c in cancellations if c["name"] not in exclusions]
    save_pending(updated, pending_type="cancel")

    excluded_names = "\n".join([f"• {name}" for name in exclusions])
    remaining_names = "\n".join([f"• {c['name']}" for c in updated]) or "nobody"

    logger.info(f"Excluded: {exclusions}. Remaining: {len(updated)}.")
    await update.message.reply_text(
        f"✅ Excluded from list:\n{excluded_names}\n\nRemaining for cancellation:\n{remaining_names}"
    )


# ─── Run bot ──────────────────────────────────────────────────────────────────

def run_bot():
    logger.info("Starting Telegram bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot is running, waiting for events...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()