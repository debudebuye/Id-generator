# 🚀 Quick Telegram Bot Setup Guide

## ✅ What's New

Your Telegram bot now has **ALL** the functionality of the web interface:

### 🆕 New Features Added:
- **📸 Custom Photo Upload** - Upload your own photo or use PDF photo
- **✏️ Individual Field Editing** - Edit any personal information field
- **🏠 Address Editing** - Modify region, subcity, woreda information  
- **🌍 Nationality Editing** - Update nationality in both languages
- **🆔 Mini ID Generation** - Generate mini ID cards
- **🆔 Old ID Generation** - Generate old ID cards
- **📋 Comprehensive Data Review** - Review all data before generation
- **⚙️ Advanced Generation Options** - Background removal and ID type selection
- **🔒 User Access Control** - Restrict bot access to specific users

## 🔧 Setup Instructions

### 1. Get Your Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow instructions
3. Copy your bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure Environment
Create or update your `.env` file in the project root:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. (Optional) Set Up User Access Control
To restrict bot access to specific users:

#### Option A: Using the User ID Finder Script
```bash
python get_telegram_user_id.py
```
Then add the User ID to your `.env` file:
```bash
ALLOWED_USER_IDS=123456789
```

#### Option B: Manual User ID Finding
1. Open Telegram and search for `@userinfobot`
2. Send `/start` to get your User ID
3. Add to `.env` file:
```bash
ALLOWED_USER_IDS=123456789,987654321
```

### 4. Run the Bot
```bash
python run_telegram_bot.py
```

## 📱 How to Use

1. **Start**: Send `/start` to your bot
2. **FIN**: Send your 12-digit FIN number
3. **PDF**: Upload your official PDF document
4. **Photo**: Choose PDF photo or upload custom photo
5. **Options**: Select background removal and ID type
6. **Review**: Review and edit all extracted data
7. **Generate**: Create your ID cards

## 🎯 Bot Commands
- `/start` - Start the process
- `/help` - Show help
- `/cancel` - Cancel current session

## 🔒 Access Control

### Open Access (Default)
If no `ALLOWED_USER_IDS` is set, the bot is open to all users.

### Restricted Access
Set `ALLOWED_USER_IDS` in your `.env` file:
```bash
# Single user
ALLOWED_USER_IDS=123456789

# Multiple users (comma-separated)
ALLOWED_USER_IDS=123456789,987654321,555666777
```

### Security Features
- ✅ User ID validation at every interaction
- ✅ Clear access denied messages
- ✅ User ID display for easy identification
- ✅ Session cleanup for unauthorized users

## 🔄 Complete Workflow

The bot now provides a **complete mobile-friendly alternative** to the web interface:

### Data Extraction
- ✅ Automatic PDF data extraction
- ✅ Support for all PDF formats (default, residential_sheger, demographic)
- ✅ Fallback mechanism for missing data

### Photo Management
- ✅ Extract photo from PDF
- ✅ Upload custom photo
- ✅ Background removal options (white/black)

### Data Editing
- ✅ Edit personal information (names, DOB, gender, phone)
- ✅ Edit address information (region, subcity, woreda)
- ✅ Edit nationality information
- ✅ Real-time data validation

### ID Generation
- ✅ Normal ID cards (front/reverse, color/grayscale)
- ✅ Mini ID cards (front only, color/grayscale)
- ✅ Old ID cards (front/reverse, color/grayscale)
- ✅ QR codes and barcodes

### User Experience
- ✅ Interactive inline keyboards
- ✅ Step-by-step guided process
- ✅ Comprehensive data review
- ✅ Error handling and recovery
- ✅ Access control and security

## 🛠️ Utility Scripts

### User ID Finder
```bash
python get_telegram_user_id.py
```
This script helps you find your Telegram User ID for access control.

### Bot Runner
```bash
python run_telegram_bot.py
```
Main script to run the bot with all features.

## 🚀 Ready to Use!

Your Telegram bot is now a **complete frontend** for the Fyda ID generator with all web interface functionality and **enterprise-grade security**!

---

**Note**: The bot uses the same core services as the web interface, so all improvements and bug fixes are automatically available in both interfaces.
