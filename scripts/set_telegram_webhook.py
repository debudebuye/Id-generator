#!/usr/bin/env python3
"""One-off script: point Telegram at the Cloud Run webhook instead of polling.

Run once after deploying (and again any time the Cloud Run URL or the secret
changes):

    PUBLIC_URL=https://<service>-<hash>-<region>.a.run.app \
    python scripts/set_telegram_webhook.py

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET from the environment/.env,
same as the app does.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from telegram_bot.bot import build_telegram_client

load_dotenv()


async def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
    public_url = os.environ.get('PUBLIC_URL')

    missing = [name for name, val in [
        ('TELEGRAM_BOT_TOKEN', token),
        ('TELEGRAM_WEBHOOK_SECRET', secret),
        ('PUBLIC_URL', public_url),
    ] if not val]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    url = f"{public_url.rstrip('/')}/telegram/webhook/{secret}"

    bot = build_telegram_client()
    async with bot:
        ok = await bot.set_webhook(url=url, secret_token=secret, drop_pending_updates=True)
        print(f"setWebhook -> {ok}\nurl -> {url}")
        info = await bot.get_webhook_info()
        print(info)


if __name__ == '__main__':
    asyncio.run(main())
