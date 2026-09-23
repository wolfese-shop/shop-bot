import asyncio
import os
from aiohttp import web

from app.bot import run_bot


async def health(request):
    return web.Response(text="Vulfis is running!")


async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"🌐 Web server started on port {port}")

    while True:
        await asyncio.sleep(3600)


async def main():
    print("🐺 Vulfis запускается...")

    await asyncio.gather(
        run_bot(),
        start_web(),
    )


if __name__ == "__main__":
    asyncio.run(main())
