# hoyo-codes

 API to get gift codes from Hoyoverse games, made for auto code redemption feature in [hoyo buddy](https://github.com/seriaati/hoyo-buddy).  

## Endpoints

- Genshin: <https://hoyo-codes.seriaati.xyz/codes?game=genshin>
- Honkai Star Rail: <https://hoyo-codes.seriaati.xyz/codes?game=hkrpg>
- Honkai Impact 3rd: <https://hoyo-codes.seriaati.xyz/codes?game=honkai3rd>
- Zenless Zone Zero: <https://hoyo-codes.seriaati.xyz/codes?game=nap>

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

- `update.py` to run once every 2 hours
- `check.py` to run once everyday

## Notes

Unfortunately, the status of Honkai Impact 3rd codes cannot be verified, as this game doesn't support redeeming codes through websites.  
Also, this service can't be made for the Chinese region as it also doesn't support redeeming codes through websites.
