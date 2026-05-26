#!/usr/bin/env python3
"""
Telegram Bot Runner for Fyda ID Card Generator
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot.bot import FydaTelegramBot

def parse_allowed_user_ids(env_value: str) -> list:
    """Parse allowed user IDs from environment variable"""
    if not env_value:
        return []
    
    try:
        # Split by comma and convert to integers
        user_ids = [int(uid.strip()) for uid in env_value.split(',') if uid.strip()]
        return user_ids
    except ValueError as e:
        print(f"❌ Error parsing ALLOWED_USER_IDS: {e}")
        print("Please use comma-separated integers (e.g., '123456789,987654321')")
        return []

def main():
    """Main function to run the Telegram bot"""
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ALLOWED_USER_IDS_STR = os.getenv('ALLOWED_USER_IDS', '')
    
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        print("Please set your Telegram bot token in a .env file:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        sys.exit(1)
    
    # Parse allowed user IDs
    allowed_user_ids = parse_allowed_user_ids(ALLOWED_USER_IDS_STR)
    
    try:
        print("🤖 Starting Fyda Telegram Bot...")
        print("📱 Bot features:")
        print("   • PDF data extraction")
        print("   • Custom photo upload")
        print("   • Background removal options")
        print("   • Individual field editing")
        print("   • Multiple ID types (normal, mini, old)")
        print("   • Address and nationality editing")
        print("   • Comprehensive data review")
        
        # Show access control status
        if allowed_user_ids:
            print(f"🔒 Access restricted to {len(allowed_user_ids)} authorized users:")
            for uid in allowed_user_ids:
                print(f"   • User ID: {uid}")
        else:
            print("🌐 Access open to all users")
        
        print("\n🚀 Bot is running... Press Ctrl+C to stop")
        
        bot = FydaTelegramBot(BOT_TOKEN, allowed_user_ids=allowed_user_ids)
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
