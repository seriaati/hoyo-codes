# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

hoyo-codes is an API for fetching gift codes for Hoyoverse games (Genshin Impact, Honkai Star Rail, Zenless Zone Zero). It scrapes codes from multiple sources, verifies them via HoYoLAB redemption, and serves them through a FastAPI endpoint.

## Commands

### Development
```bash
# Install dependencies (uses uv package manager)
uv sync

# Generate Prisma client (required after schema changes)
uv run prisma generate

# Run the API server (port 1078)
python run.py

# Fetch and save new codes from sources
python update.py

# Check status of existing codes (mark expired as NOT_OK)
python check.py
```

### Linting and Type Checking
```bash
# Ruff for linting (configured via ruff defaults)
ruff check .

# Pyright for type checking (configured in pyproject.toml)
pyright
```

### Production
```bash
# Uses PM2 for process management
pm2 start pm2.json
```

## Architecture

### Entry Points
- `run.py` - Starts the FastAPI server via uvicorn
- `update.py` - Scheduled task (hourly) to fetch new codes from web sources
- `check.py` - Scheduled task (daily) to verify existing codes are still valid

### Core Flow
1. **Scraping** ([api/codes/sources.py](api/codes/sources.py)) - Defines CODE_URLS mapping games to source websites
2. **Parsing** ([api/codes/parsers.py](api/codes/parsers.py)) - BeautifulSoup parsers for each source (gamesradar, pockettactics, fandom wikis, hoyolab API)
3. **Verification** ([api/codes/status_verifier.py](api/codes/status_verifier.py)) - Attempts code redemption via genshin.py to determine validity
4. **Storage** - PostgreSQL via Prisma ORM, schema in `schema.prisma`
5. **API** ([api/app.py](api/app.py)) - FastAPI endpoints serving codes with status=OK

### Database Schema
- `RedeemCode` model with fields: id, code, status (OK/NOT_OK), game, rewards
- Game enum: genshin, hkrpg (Star Rail), nap (ZZZ), honkai3rd, tot (deprecated)

### Key Dependencies
- `genshin.py` - HoYoLAB client for code verification (installed from git master branch)
- `prisma` - Database ORM
- `beautifulsoup4` + `lxml` - HTML parsing
- `fake-useragent` - Required for pockettactics (blocks without user-agent)

### Configuration
- `cookies.json` - HoYoLAB cookies per game for code verification
- `DATABASE_URL` env var - PostgreSQL connection string
- `API_TOKEN` env var - Bearer token for protected endpoints (POST/DELETE)
