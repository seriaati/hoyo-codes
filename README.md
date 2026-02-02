# hoyo-codes

 API to get gift codes for Hoyoverse games, made for auto code redemption feature in [Hoyo Buddy](https://github.com/seriaati/hoyo-buddy).  

 Besides an API, there is also a simple site for displaying all the available codes: <https://hoyo-codes.seria.moe>.

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

 1. We first use `aiohttp` to get the website's HTML.
 2. Then we parse the HTML using `beautifulsoup` + `lxml` (for faster parsing), then extract the codes from the website by inspecting the HTML elements
 3. Next we verify the status of the each code with `genshin.py`, we would request to HoYoLAB to redeem a specific code, and save the code with different `CodeStatus` (OK or NOT_OK) based on the redemption result. If the code already exists in the database, we would skip the verification process

### check.py

1. We get all the codes in the database with `CodeStatus.OK` and verify their status with the same technique used in `update.py`
2. Update the code with the new status

### API

The API grabs the codes from the database with `CodeStatus.OK` and game with the game requested.

You can send POST and DELETE requests to `/codes` endpoint to add or remove codes manually, but you would need to provide the `API_TOKEN` in the `Authorization` header using the `Bearer` scheme. See the `/docs` endpoint for more details.

### Scheduled Task

The API runs on my machine, and I schedule 2 tasks:

- `update.py` to run once every 1 hours
- `check.py` to run once everyday

You can send POST requests to `/update-codes` and `/check-codes` endpoints to manually trigger these tasks.

> [!NOTE]
> Since v2.4.0, the scheduled tasks are now run inside the API using `APScheduler`, so you don't need to set up cron jobs or anything similar anymore.

### Same Family Code Detection

Same family codes are codes that share the same prefix (ZZZ25, ZZZ24, etc.) and only one code from the same family can be redeemed per account. This pattern is currently only observed in Zenless Zone Zero codes.

Because Hoyo doesn't return any special errors to indicate that a code is invalid due to another code from the same family already being redeemed (it returns "code redeemed", which is treated as a `OK` in hoyo-codes), it is a bit tricky to detect such cases. This is how hoyo-codes handles it:

When checking the status of a code, if the code is found to be valid (either redeem successful or already redeemed), we check if there are any other codes in the database that share the same prefix AND it is not the code itself that's beind checked AND the the status is `OK`.

If such codes exist, we mark the status of the code being checked as `NOT_OK`, since it cannot be redeemed due to another code from the same family already being redeemed.

Below is an example scenario:

First time when a code of a family is redeemed, and it is a valid code:

1. Since no other codes of the family is in the database, `same_family_code_exists` returns `False`.
2. The code is marked as `OK`.

Later, when checking another code from the same family that is also valid:

1. `same_family_code_exists` returns `True` since there is already a code from the same family in the database with `OK`.
2. The code is marked as `NOT_OK`.

Later, when checking the first code again in the `check-codes` task:

1. If the code is still valid, `same_family_code_exists` returns `False` since there is no another code from the same family in the database with `OK` (excluding itself).
2. If the code is no longer valid, it is marked as `NOT_OK` as usual.

## Self-Hosting

### Option 1: Docker Compose (Recommended)

This method bundles PostgreSQL database with the API for easy setup:

1. Download [docker-compose.yml](https://raw.githubusercontent.com/seriaati/hoyo-codes/main/docker-compose.yml).
2. Create a `cookies.json` file in the same directory ([see format](#cookiesjson-format)).
3. Create a `uids.json` file in the same directory ([see format](#uidsjson-format)).
4. Change `API_TOKEN` and `POSTGRES_PASSWORD` in `docker-compose.yml`.
5. Run `docker compose up -d`.

The API will be available at `http://localhost:1078`.

> [!NOTE]
> You can change the `HOST` and `PORT` environment variables in `docker-compose.yml` to bind to different interfaces or ports.

### Option 2: Docker Image Only

If you have an existing PostgreSQL database:

1. Create a `cookies.json` file ([see format](#cookiesjson-format))
2. Create a `uids.json` file ([see format](#uidsjson-format))
3. Run the container:

```bash
docker run -d \
  --name hoyo-codes \
  -p 1078:1078 \
  -e DATABASE_URL="postgresql://user:password@host:5432/dbname" \
  -e API_TOKEN="your_api_token" \
  -e HOST="0.0.0.0" \
  -e PORT="1078" \
  -v ./cookies.json:/app/cookies.json \
  -v ./uids.json:/app/uids.json \
  -v hoyo-codes-logs:/app/logs \
  ghcr.io/seriaati/hoyo-codes:latest
```

Replace `DATABASE_URL` with your PostgreSQL connection string. Change `API_TOKEN` to something secure.

> [!NOTE]
> You can change the `HOST` and `PORT` environment variables to bind to different interfaces or ports.

### cookies.json Format

```json
{
  "genshin": "stoken=...; ltoken_v2=...; ltuid_v2=...",
  "hkrpg": "...",
  "nap": "..."
}
```

You need game accounts that are eligible to redeem codes (e.g. adventure rank 10+ for Genshin Impact) for the corresponding games, then link them to your Hoyoverse account to get the cookies.

`stoken` is essentially required because without it the cookie_token will expire very quickly. `stoken` is a special cookie obtained by logging in with email/username and password, it lasts for a long period of time (usually a year), it can be used to generate new `cookie_token`s.

Below is a snippet to get the cookies needed via [genshin.py](https://github.com/thesadru/genshin.py):

```py
import genshin

client = genshin.Client()
cookies = await client.login_with_app_password("me@gmail.com", "EheTeNandayo")
print(cookies.to_str())
```

If you have one Hoyoverse account linked to multiple game accounts, you just have to copy paste the same cookies for those games.

### uids.json Format

```json
{
  "genshin": 123456789,
  "hkrpg": 987654321,
  "nap": 192837465
}
```

### Volumes

- `./cookies.json:/app/cookies.json`: Mount your cookies file
- `./uids.json:/app/uids.json`: Mount your uids file
- `hoyo-codes-logs:/app/logs`: Persistent logs volume

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `API_TOKEN`: (Optional) Token for authenticating API requests
- `HOST`: Host to bind the API to
- `PORT`: Port to bind the API to
- `PROXY_URL`: (Optional) Proxy URL for outbound requests

## Extra Information

> [!WARNING]
> Honkai Impact 3rd and Tears of Themis endpoints are deprecated, they won't be removed, but no new codes will be added.

Honkai Impact 3rd and Tears of Themis code status cannot be verified. For Hi3, codes can't be redeemed on the website, and for ToT, I don't have a game account for it. The status of codes for these two games will always be `CodeStatus.OK`.
For CN region, they can only redeem codes in-game, so this service is not possible for them.
