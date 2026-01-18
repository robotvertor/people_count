import asyncio
from telegram import Bot

TELEGRAM_TOKEN = "8324375966:AAGJi5dFA8dlz97n91w6ZzlxaVzLK02bpx0"  # Ваш токен
bot = Bot(token=TELEGRAM_TOKEN)

async def get_chat_id():
    updates = await bot.get_updates()
    for update in updates:
        if update.message:  # Check if the update contains a message
            print(update.message.chat.id)

asyncio.run(get_chat_id())