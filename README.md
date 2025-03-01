# hoyo-codes

 API to get gift codes for Hoyoverse games, made for auto code redemption feature in [Hoyo Buddy](https://github.com/seriaati/hoyo-buddy).  

## Endpoints

- Genshin: <https://hoyo-codes.seria.moe/codes?game=genshin>
- Honkai Star Rail: <https://hoyo-codes.seria.moe/codes?game=hkrpg>
- Honkai Impact 3rd: <https://hoyo-codes.seria.moe/codes?game=honkai3rd> **[DEPRECATED]**
- Zenless Zone Zero: <https://hoyo-codes.seria.moe/codes?game=nap>
- Tears of Themis: <https://hoyo-codes.seria.moe/codes?game=tot> **[DEPRECATED]**

## How it Works

- The `run.py` file is responsible for running the API
- The `update.py` file is used to fetch codes from the sources listed in `/api/codes/sources.py`
- The `check.py` file is used to check the status of old codes to see if they have expired

### update.py

 1. We first use `aiohttp` to get the website's HTML. For pockettactics you would need a user agent, else the website blocks you, this is why the `fake-useragent` package is used
 2. Then we parse the HTML using `beautifulsoup` + `lxml` (for faster parsing), then extract the codes from the website by inspecting the HTML elements
 3. Next we verify the status of the each code with `genshin.py`, we would request to HoYoLAB to redeem a specific code, and save the code with different `CodeStatus` (OK or NOT_OK) based on the redemption result. If the code already exists in the database, we would skip the verification process

### check.py

1. We get all the codes in the database with `CodeStatus.OK` and verify their status with the same technique used in `update.py`
2. Update the code with the new status

### API

The API grabs the codes from the database with `CodeStatus.OK` and game with the game requested

### Scheduled Task

The API runs on my machine, and I schedule 2 tasks:

- `update.py` to run once every 1 hours
- `check.py` to run once everyday

## Notes

> [!WARNING]
> Honkai Impact 3rd and Tears of Themis endpoints are deprecated, they won't be removed, but no new codes will be added.

Honkai Impact 3rd and Tears of Themis code status cannot be verified. For Hi3, codes can't be redeemed on the website, and for ToT, I don't have a game account for it. The status of codes for these two games will always be `CodeStatus.OK`.  
For CN region, they can only redeem codes in-game, so this service is not possible for them.
