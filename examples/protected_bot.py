"""Пример защищённого Telegram-бота с Shieldgram.

Запуск:
    1. Подними Redis: docker run -d -p 6379:6379 redis:7-alpine
    2. Установи BOT_TOKEN в переменные окружения
    3. Запусти: python examples/protected_bot.py
"""

import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from shieldgram import Shield

router = Router(name="main")

BOT_TOKEN = os.environ["BOT_TOKEN"]

shield = Shield(
    redis="redis://localhost:6379/0",
    rate_limiter={
        "sliding_window_seconds": 60,
        "max_requests_per_window": 30,
        "token_bucket_rate": 5,
        "token_bucket_burst": 10,
    },
    flood_detector={
        "burst_window_seconds": 5,
        "burst_threshold": 10,
        "repeat_window_seconds": 30,
        "repeat_threshold": 5,
    },
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "\U0001f6e1\ufe0f **Shieldgram** is protecting this bot.\n\n"
        "Try spamming me — you'll get blocked!"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Send me any message and I'll echo it back.")


@router.message()
async def echo(message: Message) -> None:
    await message.answer(f"You wrote: {message.text}")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(shield)
    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await shield.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
