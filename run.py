from __future__ import annotations

import asyncio
from contextlib import suppress

import uvicorn

from api.app import app

if __name__ == "__main__":
    with suppress(KeyboardInterrupt, asyncio.CancelledError):
        uvicorn.run(app, host="0.0.0.0", port=1078, log_config=None, log_level=None)  # noqa: S104
