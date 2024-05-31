import asyncio
from contextlib import suppress

import uvicorn

from api.app import app

if __name__ == "__main__":
    with suppress(KeyboardInterrupt, asyncio.CancelledError):
        uvicorn.run(app, port=1078)
