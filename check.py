from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from api.codes.task import check_codes

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(check_codes())
