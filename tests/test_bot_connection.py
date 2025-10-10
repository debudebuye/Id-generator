#!/usr/bin/env python3
"""
Test if the bot is running and responding
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the telegram_bot directory to the path
sys.path.append('telegram_bot')

from telegram_bot.bot import FydaTelegramBot

async def test_bot_connection():
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
    
    print(f"Bot token: {token[:10]}...")
    print(f"Allowed user IDs: {allowed_user_ids}")
    print(f"Restrict access: {bot.restrict_access}")
    
    # Test with a user that should NOT be authorized
    test_user_id = 123456789  # This should not be in the allowlist
    print(f"\nTesting with unauthorized user ID: {test_user_id}")
    print(f"Is authorized: {bot.is_user_authorized(test_user_id)}")
    
    if not bot.is_user_authorized(test_user_id):
        print("✅ User is correctly identified as unauthorized")
        print("This user should trigger the new user notification")
        
        # Test the notification function
        print("\nTesting notification function...")
        class MockContext:
            pass
        
        await bot._notify_admins_new_user(MockContext(), test_user_id, "Test User", "testuser")
        print("✅ Notification function completed")
    else:
        print("❌ User is incorrectly identified as authorized")
        print("This means the allowlist is not working properly")

if __name__ == "__main__":
    asyncio.run(test_bot_connection())
