# 🤖 Fyda Telegram Bot

A comprehensive Telegram bot that provides all the functionality of the web interface for generating Ethiopian Digital ID cards.

## 🚀 Features

### Core Functionality
- **PDF Data Extraction**: Automatically extract personal information from official PDF documents
- **Custom Photo Upload**: Upload your own photo or use the one from the PDF
- **Background Removal**: Remove white or black backgrounds from photos
- **Multiple ID Types**: Generate normal, mini, and old ID cards

### Data Management
- **Individual Field Editing**: Edit any personal information field
- **Address Editing**: Modify region, subcity, and woreda information
- **Nationality Editing**: Update nationality in both languages
- **Comprehensive Review**: Review all data before generation

### User Experience
- **Interactive Menus**: Easy-to-use inline keyboards
- **Step-by-Step Process**: Guided workflow from start to finish
- **Real-time Feedback**: Immediate confirmation of actions
- **Error Handling**: Clear error messages and recovery options

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
3. **Project Dependencies** installed (see main README)

## 🔧 Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Install Dependencies

Make sure all project dependencies are installed:

```bash
pip install -r requirements.txt
```

## 🚀 Running the Bot

### Option 1: Using the Runner Script (Recommended)

```bash
python run_telegram_bot.py
```

### Option 2: Direct Execution

```bash
python telegram_bot/bot.py
```

## 📱 How to Use

### 1. Start the Bot
- Open Telegram and search for your bot
- Send `/start` to begin

### 2. Provide FIN Number
- Send your 12-digit FIN number
- Example: `123456789012`

### 3. Upload PDF Document
- Upload your official PDF document
- The bot will automatically extract data

### 4. Choose Photo Option
- **Use PDF Photo**: Use the photo extracted from the PDF
- **Upload Custom Photo**: Upload your own photo

### 5. Configure Generation Options
- **Background Removal**: Choose white/black background removal
- **ID Type**: Select normal, mini, or old ID cards

### 6. Review and Edit Data
- Review all extracted information
- Edit any fields as needed:
  - Personal information (names, DOB, gender, phone)
  - Address information (region, subcity, woreda)
  - Nationality information

### 7. Generate ID Cards
- Click "Generate ID Cards" to create your digital IDs
- Receive all generated images in the chat

## 🎯 Bot Commands

- `/start` - Start the ID generation process
- `/help` - Show help information
- `/cancel` - Cancel current session

## 🔄 Workflow States

The bot operates in the following states:

1. **WAITING_FOR_FIN** - Waiting for 12-digit FIN number
2. **WAITING_FOR_PDF** - Waiting for PDF document upload
3. **WAITING_FOR_PHOTO** - Waiting for photo choice or upload
4. **WAITING_FOR_BG_OPTION** - Waiting for background removal choice
5. **WAITING_FOR_CITY_TYPE** - Waiting for address format selection
6. **CONFIRMING_DATA** - Reviewing and editing extracted data
7. **WAITING_FOR_FIELD_VALUE** - Waiting for field value input

## 🛠️ Technical Details

### File Structure
```
telegram_bot/
├── bot.py              # Main bot implementation
├── README.md           # This file
└── __init__.py         # Package initialization
```

### Key Components

- **FydaTelegramBot**: Main bot class handling all interactions
- **ConversationHandler**: Manages the conversation flow
- **InlineKeyboardMarkup**: Provides interactive buttons
- **Session Management**: Stores user data during the process

### Integration with Web Interface

The bot uses the same core services as the web interface:
- `IDCardService` for PDF extraction and ID generation
- Same configuration and templates
- Identical data processing logic

## 🔧 Customization

### Adding New Fields

To add new editable fields:

1. Add field name to `EDITABLE_FIELDS` list in `bot.py`
2. Update the data review display in `show_data_review()`
3. Add field to appropriate edit category (personal, address, nationality)

### Modifying Generation Options

To add new generation options:

1. Add new callback data in `show_generation_options()`
2. Handle the option in `handle_bg_option()`
3. Update the data review display

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if bot token is correct
   - Verify bot is running without errors
   - Check internet connection

2. **PDF upload fails**
   - Ensure PDF is valid and not corrupted
   - Check file size (should be reasonable)
   - Verify PDF contains extractable text

3. **Photo upload issues**
   - Ensure photo is in supported format (JPEG/PNG)
   - Check file size
   - Try using PDF photo instead

4. **Generation fails**
   - Check if all required fields are filled
   - Verify static folder permissions
   - Check server logs for detailed errors

### Debug Mode

To enable debug logging, modify the bot initialization:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main project documentation
3. Check server logs for detailed error messages

## 🔄 Updates

The bot automatically uses the latest features from the main application:
- New PDF formats are automatically supported
- Template updates are reflected immediately
- Service improvements are inherited automatically

---

**Note**: This bot provides the same functionality as the web interface but in a more accessible, mobile-friendly format through Telegram. 