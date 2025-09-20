#!/usr/bin/env python3
"""
Utility script to get Telegram User ID for bot access control
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_user_id_from_bot():
    """Get user ID by creating a simple bot that responds with the user's ID"""
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes
        
        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not BOT_TOKEN:
            print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
            print("Please set your Telegram bot token in a .env file first.")
            return
        
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            user_id = user.id
            first_name = user.first_name or "Unknown"
            username = user.username or "No username"
            
            message = (
                f"👋 Hello {first_name}!\n\n"
                f"📋 *Your Telegram User Information:*\n\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"👤 **Name:** {first_name}\n"
                f"📛 **Username:** @{username}\n\n"
                f"💡 *To restrict bot access:*\n"
                f"Add this to your .env file:\n"
                f"`ALLOWED_USER_IDS={user_id}`\n\n"
                f"🔗 *For multiple users:*\n"
                f"`ALLOWED_USER_IDS={user_id},123456789,987654321`"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            help_text = (
                "*User ID Finder Bot*\n\n"
                "This bot helps you find your Telegram User ID for access control.\n\n"
                "*Commands:*\n"
                "/start - Get your User ID\n"
                "/help - Show this help message\n\n"
                "*Usage:*\n"
                "1. Send /start to get your User ID\n"
                "2. Copy the User ID from the response\n"
                "3. Add it to your .env file for bot access control"
            )
            await update.message.reply_text(help_text, parse_mode='Markdown')
        
        # Create and run the bot
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        print("🔍 Starting User ID Finder Bot...")
        print("📱 Instructions:")
        print("1. Open Telegram and search for your bot")
        print("2. Send /start to get your User ID")
        print("3. Copy the User ID from the response")
        print("4. Add it to your .env file")
        print("\n🚀 Bot is running... Press Ctrl+C to stop")
        
        application.run_polling()
        
    except ImportError:
        print("❌ Error: python-telegram-bot not installed.")
        print("Please install it with: pip install python-telegram-bot")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

def manual_instructions():
    """Show manual instructions for finding User ID"""
    print("📋 Manual Instructions to Find Your Telegram User ID:")
    print("\n1️⃣ **Using @userinfobot (Recommended):**")
    print("   • Open Telegram and search for @userinfobot")
    print("   • Send /start to the bot")
    print("   • It will reply with your User ID")
    print("\n2️⃣ **Using @RawDataBot:**")
    print("   • Open Telegram and search for @RawDataBot")
    print("   • Send any message to the bot")
    print("   • Look for 'id' field in the response")
    print("\n3️⃣ **Using this script:**")
    print("   • Make sure you have TELEGRAM_BOT_TOKEN in your .env file")
    print("   • Run: python get_telegram_user_id.py")
    print("   • Send /start to your bot")
    print("\n💡 **User ID Format:**")
    print("   • User IDs are numbers (e.g., 123456789)")
    print("   • They are unique for each Telegram user")
    print("   • They don't change unless you delete and recreate your account")

def main():
    """Main function"""
    print("🔍 Telegram User ID Finder")
    print("=" * 40)
    
    # Check if bot token is available
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if BOT_TOKEN:
        print("✅ Bot token found in .env file")
        print("🚀 Starting User ID Finder Bot...")
        print()
        get_user_id_from_bot()
    else:
        print("❌ Bot token not found in .env file")
        print("📝 Showing manual instructions instead...")
        print()
        manual_instructions()
        
        print("\n" + "=" * 40)
        print("🔧 **To use this script:**")
        print("1. Add your bot token to .env file:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("2. Run this script again:")
        print("   python get_telegram_user_id.py")

if __name__ == "__main__":
    main()
