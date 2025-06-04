from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from api.codes.task import update_codes

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(update_codes())
