import asyncio
from telegram import Bot

TELEGRAM_TOKEN = ""  # Ваш токен
bot = Bot(token=TELEGRAM_TOKEN)

async def get_chat_id():
    updates = await bot.get_updates()
    for update in updates:
        if update.message:  # Check if the update contains a message
            print(update.message.chat.id)

asyncio.run(get_chat_id())
