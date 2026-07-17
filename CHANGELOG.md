# Changelog

All notable changes to Shieldgram will be documented in this file.

## [0.1.0] — 2026-07-17

### Added
- **Rate Limiter** — Sliding Window + Token Bucket with atomic Lua scripts in Redis
- **Flood Detector** — Burst frequency analysis + repeated content detection
- **Threat Score Engine** — Weighted scoring (flood +0.4, spam +0.3, links +0.2, suspicious +0.1)
- **Detection Engine** — Concurrent detector orchestration with `asyncio.gather`
- **Decision Engine** — Worst-case aggregation (BLOCK > WARN > ALLOW)
- **Shield Middleware** — aiogram 3 `BaseMiddleware` with one-line integration
- **Redis Storage** — `RedisStorage` backend with hiredis and connection pooling
- **Abstract Storage** — Pluggable storage interface for future backends
- **Configuration** — Dataclass-based config with `from_dict()` factory
- **Examples** — `protected_bot.py` + `attack_simulator.py`
- **GitHub Actions CI** — pytest + mypy + ruff on Python 3.11 and 3.12
- **Docker** — `docker-compose.yml` with Redis + bot setup
- **PyPI** — Published as `shieldgram`

[0.1.0]: https://github.com/fvckxd55/Shieldgram/releases/tag/v0.1.0
