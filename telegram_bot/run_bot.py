#!/usr/bin/env python3
"""
Fyda Digital ID Generator - Telegram Bot Launcher

This script launches the Telegram bot with proper error handling and environment checks.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'telegram',
        'dotenv',
        'PIL',
        'fitz',
        'qrcode'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'telegram':
                import telegram
            elif package == 'dotenv':
                import dotenv
            elif package == 'PIL':
                import PIL
            elif package == 'fitz':
                import fitz
            elif package == 'qrcode':
                import qrcode
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if environment variables are set."""
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found.")
        print("Please create a .env file with your TELEGRAM_BOT_TOKEN:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        return False
    
    return True

def main():
    """Main launcher function."""
    print("🤖 Fyda Digital ID Generator - Telegram Bot")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ All checks passed!")
    print("🚀 Starting Telegram bot...")
    print("-" * 50)
    
    try:
        # Import and run the bot
        from bot import FydaTelegramBot
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        bot = FydaTelegramBot(token)
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 