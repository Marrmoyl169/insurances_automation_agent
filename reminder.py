import asyncio
from datetime import date
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from memory import get_groups_to_ask
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def send_reminders():
    groups = get_groups_to_ask()
    if not groups:
        print("No groups to remind today.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)

    for group in groups:
        lines = []
        for c in group["cancellations"]:
            lines.append(f"• {c['name']} ({c['agreement']})")
        insurance_list = "\n".join(lines)

        text = (
            f"📋 *{group['sent_date']}* you sent a cancellation for:\n"
            f"{insurance_list}\n\n"
            f"Did Michal confirm the cancellation?"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirmed:{group['id']}"),
                InlineKeyboardButton("⏳ Tomorrow", callback_data=f"postpone:{group['id']}")
            ]
        ])

        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        print(f"Reminder sent for group {group['id']}")

if __name__ == "__main__":
    asyncio.run(send_reminders())