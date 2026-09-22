import asyncio
from threading import Thread
import uvicorn
from .db import init_db
from .bot import run_bot
from .web import app

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    await init_db()
    Thread(target=run_web, daemon=True).start()
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
