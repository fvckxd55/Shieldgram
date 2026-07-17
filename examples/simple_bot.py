"""Пример Telegram-бота с BotShield-защитой.

Запуск:
    1. Подними Redis: docker run -d -p 6379:6379 redis:7-alpine
    2. Установи BOT_TOKEN в переменные окружения
    3. Запусти: python examples/simple_bot.py
"""

import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from botshield import BotShield

router = Router(name="main")

BOT_TOKEN = os.environ["BOT_TOKEN"]

shield = BotShield(
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
    block_threshold=0.8,
    warn_threshold=0.5,
    ignore_users=os.environ.get("BOT_ADMINS", "").split(","),
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer("Привет! Я бот с защитой BotShield.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Я просто отвечаю на любое сообщение. Попробуй отправить что-нибудь!")


@router.message()
async def echo(message: Message) -> None:
    await message.answer(f"Ты написал: {message.text}")


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
