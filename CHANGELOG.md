# Changelog

All notable changes to Shieldgram will be documented in this file.

## [0.2.0] — 2026-07-17

### Added
- **Spam Detector** — Link detection (URL + t.me), advertising pattern matching (casino, crypto, "buy cheap", etc.)
- **User Reputation System** — Redis-backed 0.0–1.0 scoring with penalty on attack and decay on normal behavior
- **PostgreSQL Logger** — AsyncSQLAlchemy event store for audit trails and analytics (`detection_logs` table)
- **Reputation Config** — `penalty` (0.15) and `decay` (0.95) tunable per deployment
- **Spam Config** — `max_links_per_message` (3) and `ad_pattern_threshold` (2)

### Changed
- **ShieldConfig** — Added `spam_detector`, `reputation`, and `postgres_url` fields
- **Shield middleware** — Integrated reputation engine, spam detector, and PostgreSQL logging
- Bumped test suite from 26 to 37 tests

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

[0.2.0]: https://github.com/fvckxd55/Shieldgram/releases/tag/v0.2.0
[0.1.0]: https://github.com/fvckxd55/Shieldgram/releases/tag/v0.1.0
