"""Attack simulator — демонстрация работы Shieldgram.

Отправляет шквал сообщений и показывает, как Shieldgram их блокирует.

Запуск: python examples/attack_simulator.py
"""

from __future__ import annotations

import asyncio
import time


async def simulate_attack() -> None:
    """Симуляция flood-атаки через локальные вызовы детекторов."""

    from shieldgram import Shield

    shield = Shield(
        redis="redis://localhost:6379/0",
        rate_limiter={
            "sliding_window_seconds": 60,
            "max_requests_per_window": 5,
        },
        flood_detector={
            "burst_window_seconds": 5,
            "burst_threshold": 3,
        },
    )
    await shield.startup()

    print("=" * 50)
    print("  Shieldgram Attack Simulator")
    print("=" * 50)
    print()
    print("Sending 10 rapid messages to simulate a flood attack...")
    print()

    results = []
    for i in range(10):
        start = time.monotonic()

        from aiogram.types import Chat, Message, User

        msg = Message(
            message_id=i + 1,
            date=0,
            chat=Chat(id=12345, type="private"),
            from_user=User(id=12345, is_bot=False, first_name="Attacker"),
            text="spam spam spam" if i >= 5 else f"message_{i}",
        )

        result = await shield._detection_engine.analyze(msg, {})
        elapsed = (time.monotonic() - start) * 1000

        status = "✅ ALLOW"
        for r in result:
            if r.verdict.name in ("WARN", "BLOCK"):
                status = f"⚠️  {r.verdict.name}"
                break

        print(f"  [{i+1:2d}] {status:12s} ({elapsed:.1f}ms)")
        results.append(status)
        await asyncio.sleep(0.01)

    blocks = sum(1 for r in results if "BLOCK" in r)
    warns = sum(1 for r in results if "WARN" in r)
    allows = sum(1 for r in results if "ALLOW" in r)

    print()
    print("=" * 50)
    print(f"  Results: {allows} ALLOW, {warns} WARN, {blocks} BLOCK")
    print()

    if blocks > 0:
        print("  ✅ Shieldgram successfully blocked the attack!")
    else:
        print("  ⚠️  No blocks detected. Try lowering thresholds.")

    print("=" * 50)

    await shield.shutdown()


if __name__ == "__main__":
    asyncio.run(simulate_attack())
