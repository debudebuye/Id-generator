#!/usr/bin/env python3
"""
Test script to simulate a new user starting the bot
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the telegram_bot directory to the path
sys.path.append('telegram_bot')

from telegram_bot.bot import FydaTelegramBot

async def test_new_user():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('telegram_bot/.env')
    
    # Create bot instance
    token = os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token')
    bot = FydaTelegramBot(token)
    
    # Simulate a new user (not in allowlist)
    user_id = 999999999  # This should not be in the allowlist
    user_name = "Test New User"
    username = "testnewuser"
    
    print(f"Testing with user_id: {user_id}")
    print(f"User name: {user_name}")
    print(f"Username: {username}")
    print(f"Is authorized: {bot.is_user_authorized(user_id)}")
    
    # Create a mock context and update
    class MockContext:
        pass
    
    class MockUpdate:
        def __init__(self, user_id, first_name, username):
            self.effective_user = MockUser(user_id, first_name, username)
    
    class MockUser:
        def __init__(self, user_id, first_name, username):
            self.id = user_id
            self.first_name = first_name
            self.username = username
    
    # Test the notification function directly
    context = MockContext()
    await bot._notify_admins_new_user(context, user_id, user_name, username)
    
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_new_user())
