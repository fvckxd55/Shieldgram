# BotShield

Open-source middleware для защиты Telegram-ботов от автоматизированных атак.

## Возможности

- **Rate Limiting** — Sliding Window + Token Bucket
- **Flood Detection** — обнаружение взрывной частоты и повторов контента
- **Подключается без изменения бизнес-логики**

## Установка

```bash
pip install botshield
```

## Быстрый старт

```python
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from botshield import BotShield

router = Router()
shield = BotShield(redis="redis://localhost:6379/0")

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer("Hello!")

async def main():
    bot = Bot(token="YOUR_BOT_TOKEN")
    dp = Dispatcher()
    dp.message.middleware(shield)
    dp.include_router(router)
    await dp.start_polling(bot)
```

## Конфигурация

```python
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
    ignore_users=[123456789],
)
```

## Docker

```bash
docker compose up -d
```

## Лицензия

MIT
