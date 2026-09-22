import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}

SUPPORT_USERNAME = "@suport_wolfese_shop"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS не найден")
