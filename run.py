import uvicorn

from api.app import app

if __name__ == "main":
    uvicorn.run(app, port=1078)
