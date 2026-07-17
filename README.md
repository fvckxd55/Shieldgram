# 🛡️ Shieldgram

[![PyPI version](https://img.shields.io/pypi/v/shieldgram?color=blue)](https://pypi.org/project/shieldgram/)
[![Python](https://img.shields.io/pypi/pyversions/shieldgram)](https://pypi.org/project/shieldgram/)
[![Tests](https://img.shields.io/github/actions/workflow/status/fvckxd55/Shieldgram/tests.yml?branch=master&label=tests)](https://github.com/fvckxd55/Shieldgram/actions)
[![License](https://img.shields.io/pypi/l/shieldgram)](https://github.com/fvckxd55/Shieldgram/blob/master/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/shieldgram)](https://pypi.org/project/shieldgram/)

**Anti-abuse security middleware for Telegram bots.**

Protect your bot from:
- ✅ Flood attacks
- ✅ Spam
- ✅ Command abuse
- ✅ Automated users

```bash
pip install shieldgram
```

## Quick Start

```python
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from shieldgram import Shield

router = Router()
shield = Shield(redis="redis://localhost:6379/0")

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

## Threat Score Engine

Shieldgram assigns a threat score to every user action:

| Signal              | Weight |
|---------------------|--------|
| Flood (burst)       | +0.40  |
| Spam (repeat)       | +0.30  |
| Too many links      | +0.20  |
| Suspicious behavior | +0.10  |

| Score    | Verdict |
|----------|---------|
| 0.0–0.4  | ALLOW   |
| 0.4–0.7  | WARN    |
| 0.7–1.0  | BLOCK   |

## Architecture

```
Telegram Update → Shield Middleware → Detection Engine
                                          │
                              ┌───────────┼───────────┐
                         RateLimiter  FloodDetector  ...
                              │           │
                              └───────────┘
                                    │
                            Threat Score Engine
                                    │
                            Decision Engine
                               │        │
                           Redis    PostgreSQL
```

## Configuration

```python
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
    block_threshold=0.7,
    warn_threshold=0.4,
    ignore_users=[123456789],
)
```

## Run the demo

```bash
docker compose up -d
```

Or locally:

```bash
pip install shieldgram
export BOT_TOKEN="your_token"
python examples/protected_bot.py
```

Then attack it:

```bash
python examples/attack_simulator.py
```

## Roadmap

- **v0.1** — Middleware, Rate Limiter, Flood Detector, Threat Scoring
- **v0.2** — Spam detection, Reputation system, PostgreSQL logs
- **v0.3** — Dashboard, API, Docker deployment
- **v1.0** — Plugin system, production hardening

## License

MIT — see [LICENSE](LICENSE)
