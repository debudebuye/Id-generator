#!/usr/bin/env python3
"""
Setup script for Telegram Bot Access Control
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with Telegram bot configuration"""
    env_path = Path(".env")
    
    print("🔐 Setting up Telegram Bot Access Control")
    print("=" * 50)
    
    # Get bot token
    bot_token = input("Enter your Telegram Bot Token (from @BotFather): ").strip()
    if not bot_token:
        print("❌ Bot token is required!")
        return False
    
    # Get allowed user IDs
    print("\n👥 Access Control Setup:")
    user_ids_input = input("Enter allowed user IDs (comma-separated, e.g., 123456789,987654321): ").strip()
    
    # Create .env content
    env_content = f"""# Environment variables for Fyda ID Card Generator
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
MAX_FILE_SIZE=16777216
LOG_LEVEL=DEBUG

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN={bot_token}

# Access Control - Comma-separated list of allowed Telegram user IDs
ALLOWED_USER_IDS={user_ids_input}
"""
    
    # Write .env file
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ .env file created successfully!")
        
        if user_ids_input:
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            print(f"🔒 Access restricted to {len(user_ids)} users")
        else:
            print("⚠️  WARNING: Access is open to ALL users!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main function"""
    print("🤖 Fyda Telegram Bot Access Control Setup")
    print("=" * 50)
    
    if Path(".env").exists():
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Setup cancelled")
            return
    
    if create_env_file():
        print("\n🎉 Setup completed!")
        print("\n📝 Next steps:")
        print("1. Run the bot: python scripts/run_telegram_bot.py")
        print("2. The bot will now only allow authorized users")
    else:
        print("\n❌ Setup failed.")

if __name__ == "__main__":
    main()

