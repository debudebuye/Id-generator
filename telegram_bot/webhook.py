"""Telegram webhook endpoint for Cloud Run.

Replaces `bot.run()` (long-polling, needs an always-on process) with an HTTPS
route Telegram pushes updates to. Registered into the main Flask app so it ships
in the same container/deploy as the web UI (see app/__init__.py).

A `telegram.Bot` + FydaTelegramBot.dispatch_update() is used directly instead of
building a full `Application`/`ConversationHandler` - see the comment on
dispatch_update() in bot.py for why: this bot's session state is already fully
externalized to Firestore, so there's nothing left for PTB's own
Application-level state tracking to do, and skipping it avoids having to wire up
a BasePersistence implementation that reloads every user's data on every request.
"""
import asyncio
import os

from flask import Blueprint, request, abort
from telegram import Bot, Update

from telegram_bot.bot import build_bot_from_env, build_telegram_client

tg_bp = Blueprint('telegram_webhook', __name__)

_WEBHOOK_SECRET = os.getenv('TELEGRAM_WEBHOOK_SECRET', '')

# Cached across warm Cloud Run invocations (same container/process reused between
# requests). Neither object holds event-loop-bound resources by itself - the
# `telegram.Bot`'s async client is opened/closed fresh inside `_handle()` on every
# call via `async with bot_client`, so reusing the Python object across the
# separate `asyncio.run()` event loops below is safe.
_bot_logic = None
_bot_client = None


def _get_bot_logic():
    global _bot_logic
    if _bot_logic is None:
        _bot_logic = build_bot_from_env()
        _bot_logic._refresh_allowlist()
    return _bot_logic


def _get_bot_client() -> Bot:
    global _bot_client
    if _bot_client is None:
        _bot_client = build_telegram_client()
    return _bot_client


@tg_bp.route('/telegram/webhook/<secret>', methods=['POST'])
def telegram_webhook(secret):
    if not _WEBHOOK_SECRET or secret != _WEBHOOK_SECRET:
        abort(404)
    # Telegram echoes this header back on every request when a secret_token was
    # set via setWebhook - checking it stops randoms from POSTing fake updates
    # even if they guess the URL.
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != _WEBHOOK_SECRET:
        abort(403)

    payload = request.get_json(force=True, silent=True)
    if not payload:
        return '', 200

    bot_logic = _get_bot_logic()
    bot_client = _get_bot_client()
    update = Update.de_json(payload, bot_client)

    asyncio.run(_handle(bot_logic, bot_client, update))
    # Always 200: a non-2xx response makes Telegram retry the same update later,
    # which would just re-run a (possibly already-applied) step. Errors are
    # logged inside dispatch_update instead of surfaced to Telegram.
    return '', 200


async def _handle(bot_logic, bot_client, update):
    async with bot_client:
        await bot_logic.dispatch_update(update, bot_client)
