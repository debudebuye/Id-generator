#!/usr/bin/env python3
"""
Admin bot for managing allowed Telegram user IDs.

Commands (restricted to admins only):
- /add <user_id>
- /remove <user_id>
- /list
"""

import os
import sys
from typing import List

# Ensure project root is on sys.path so absolute imports work when run as a script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from telegram_bot.allowlist_store import read_allowlist, add_user, remove_user


def parse_admin_ids(env_val: str) -> List[int]:
    if not env_val:
        return []
    ids: List[int] = []
    for part in env_val.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            ids.append(int(p))
        except Exception:
            pass
    # unique
    return sorted(set(ids))


class AdminBot:
    def __init__(self, token: str, admin_user_ids: List[int]):
        self.token = token
        self.admin_user_ids = set(admin_user_ids)

    def _is_admin(self, user_id: int) -> bool:
        return int(user_id) in self.admin_user_ids

    def _deny(self) -> str:
        return (
            "🚫 *Access Denied*\n\n"
            "This admin bot is restricted.\n\n"
            "@fayda\_software"
        )

    async def _ensure_admin(self, update: Update) -> bool:
        uid = update.effective_user.id
        if not self._is_admin(uid):
            await update.message.reply_text(self._deny(), parse_mode=ParseMode.MARKDOWN)
            return False
        return True

    async def cmd_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._ensure_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /add <user_id>")
            return
        try:
            user_id = int(context.args[0])
        except Exception:
            await update.message.reply_text("Invalid user_id. Must be an integer.")
            return
        new_list = add_user(user_id)
        await update.message.reply_text(
            f"✅ Added `{user_id}`. Total allowed: {len(new_list)}",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._ensure_admin(update):
            return
        if not context.args:
            await update.message.reply_text("Usage: /remove <user_id>")
            return
        try:
            user_id = int(context.args[0])
        except Exception:
            await update.message.reply_text("Invalid user_id. Must be an integer.")
            return
        new_list = remove_user(user_id)
        await update.message.reply_text(
            f"✅ Removed `{user_id}`. Total allowed: {len(new_list)}",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._ensure_admin(update):
            return
        ids = read_allowlist()
        if not ids:
            await update.message.reply_text("Allowlist is empty.")
            return
        ids_str = ", ".join(str(x) for x in ids)
        await update.message.reply_text(
            f"👥 Allowed users ({len(ids)}):\n`{ids_str}`",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._ensure_admin(update):
            return
        text = (
            "🛠️ *Fayda Admin Bot*\n\n"
            "Use these commands to manage access:\n"
            "• `/list` — show all allowed user IDs\n"
            "• `/add <user_id>` — add a user to allowlist\n"
            "• `/remove <user_id>` — remove a user from allowlist\n\n"
            "Tip: From main bot denial message, copy the shown user ID."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("add", self.cmd_add))
        app.add_handler(CommandHandler("remove", self.cmd_remove))
        app.add_handler(CommandHandler("list", self.cmd_list))
        app.run_polling()


def main():
    load_dotenv()
    token = os.getenv("ADMIN_TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ADMIN_TELEGRAM_BOT_TOKEN missing in environment.")
        sys.exit(1)
    admin_ids = parse_admin_ids(os.getenv("ADMIN_USER_IDS", ""))
    if not admin_ids:
        print("❌ ADMIN_USER_IDS missing or empty. Provide at least one admin ID.")
        sys.exit(1)
    AdminBot(token, admin_ids).run()


if __name__ == "__main__":
    main()


