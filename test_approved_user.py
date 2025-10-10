#!/usr/bin/env python3
"""
Test if approved user is now authorized
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the telegram_bot directory to the path
sys.path.append('telegram_bot')

from telegram_bot.bot import FydaTelegramBot

async def test_approved_user():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('telegram_bot/.env')
    
    # Create bot instance
    token = os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token')
    allowed_user_ids = []
    allowed_ids_env = os.getenv('ALLOWED_USER_IDS', '')
    if allowed_ids_env:
        try:
            allowed_user_ids = [int(x.strip()) for x in allowed_ids_env.split(',') if x.strip()]
        except ValueError:
            print("Warning: Invalid ALLOWED_USER_IDS format")
    
    bot = FydaTelegramBot(token, allowed_user_ids=allowed_user_ids)
    
    print(f"Initial allowed users: {bot.allowed_user_ids}")
    
    # Test with the approved user
    approved_user_id = 555555555
    print(f"\nTesting with approved user ID: {approved_user_id}")
    print(f"Is authorized: {bot.is_user_authorized(approved_user_id)}")
    
    if bot.is_user_authorized(approved_user_id):
        print("✅ Approved user is now authorized!")
        print("This user can now use the bot normally.")
    else:
        print("❌ Approved user is still not authorized")
        print("The allowlist refresh might not be working properly")

if __name__ == "__main__":
    asyncio.run(test_approved_user())
