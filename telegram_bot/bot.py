import os
import sys
import asyncio
import re
import json
from io import BytesIO
from typing import Dict, Any, List
import requests
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.constants import ParseMode
from telegram.error import TimedOut, NetworkError

# Ensure project root is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.id_card_service import IDCardService
from app.services.daily_report_service import DailyReportService
from app.services.firebase_service import firebase_service

# Translation support
TRANSLATIONS = {
    'en': {
        'welcome': "🇪🇹 *Welcome to Ethiopian Digital ID Bot*\n\nHello {name}!\n\n**How it works:**\n📄 Upload your PDF → 🔢 Send your FIN → 🎯 Get your ID\n\n**Two modes available:**\n• **Detail Mode**: Full control over all settings\n• **Default Mode**: Auto-generate with smart defaults\n\n**Click Settings to configure your preferences:**",
        'help': "🇪🇹 *Help*\n\nUse the bot in three steps:\n1) Upload your PDF\n2) Send your 12-digit FIN\n3) Review and generate your ID\n\nCommands:\n/help — help\n/cancel — cancel session\n/compress — compress large PDF\n/report — get your daily report\n\nTip: You can start by sending any message.",
        'pdf_uploaded': "✅ PDF uploaded successfully! Please send your 12-digit FIN number.",
        'settings': "⚙️ **Settings**\n\n• Background Remover: `{bg}`\n• ID Type: `{id_type}`\n• Output Variant: `{variant}`\n• Address Format: `{city}`\n• Mode: `{mode}`\n• Language: `{language}`\n\nTap to change:",
        'settings_prompt': "🔧 **Customize Your ID Generation**\n\nYou can adjust settings like background removal, ID type, output format, and more. Choose your preferences before generating your ID.",
        'bg_options': "**Background Remover Options:**\n\nChoose what background to remove from your ID photo:",
        'id_type_options': "**ID Type Options:**\n\nChoose the type of ID you want to generate:",
        'variant_options': "**Output Variant Options:**\n\nChoose the color style for your ID:",
        'city_options': "**Address Format Options:**\n\nChoose your address format (city type):",
        'mode_options': "**Mode Options:**\n\nChoose what mode you prefer:",
        'lang_options': "**Language Options:**\n\nChoose what language you prefer:",
        'ready_start': "📄 **Ready to start!**\n\nPlease upload your official PDF document.",
        'mode_detail': "Detail Mode",
        'mode_default': "Default Mode", 
        'lang_english': "English",
        'lang_amharic': "አማርኛ",
        'back': "🔙 Back",
        'close': "❌ Close",
        'access_denied': "🚫 **Access Denied**\n\nSorry, you are not authorized to use this bot.\n\nThis bot is restricted to authorized users only. If you wanna to get access, you should talk to administrators,\n\nFor Access, Contact Administrator:\n\n{safe_admin}\n\nThank you for your understanding.",
        'bot_paused': "⏸️ Bot is currently paused by admin.\n\n📊 Please wait for the bot to be resumed.\n\nFor support, contact @fayda\\_software",
        'account_paused': "⏸️ Your account has been paused by admin. Please contact @fayda\\_software for support.",
        'welcome_fallback': "Welcome! Please upload your official PDF document first.",
        'error_generating_report': "Error generating report:",
        'downloading_pdf': "🌐 Downloading your PDF from the link... Please wait.",
        'processing_pdf': "⏳ Processing data from your PDF...",
        'daily_report_no_ids': "📊 **Daily Report - {date}**\n\n👤 User: {username}\n📈 IDs Generated Today: 0\n📈 Total IDs Generated: {total_count}\n💰 Payment Due: 0 birr\n\nThank you for using our service! 🙏",
        'daily_report_with_ids': "📊 **Daily Report - {date}**\n\n👤 User: {username}\n📈 IDs Generated Today: {today_count}\n📈 Total IDs Generated: {total_count}\n💰 Payment Due: {payment_due} birr\n\n💳 Please complete your payment and attach the screenshot for admin @fayda\\_software\n\nThank you for using our service! 🙏",
        'access_granted': "🎉 **Access Granted!**\n\n✅ IDs Generated Today: {today_count}\n📈 Total Unpaid ID Generated: {total_unpaid}",
        'id_ready': "🎉 Your ID is ready! Send any message to start a new session.",
        'access_denied_short': "🚫 **Access Denied**\n\nYou are not authorized to use this bot.\nPlease contact the administrator to get access.\n\nYour User ID: `{user_id}`",
        'access_revoked': "🚫 **Access Revoked**\n\nYour access to the bot has been revoked by the administrator.\nYou can no longer use the bot to generate ID cards.\n\nIf you believe this is an error, please contact the administrator.\nContact Administrator:\n\n@fayda\\_software\n\nThank you for your understanding.",
        'processing_id': "🔄 **Processing your ID cards...**\n\n⏳ This may take a few moments.\n📱 Please wait while I generate your images...",
        'photo_sent': "Photo sent. You can replace it or continue.",
        'choose_background': "Choose your background removal option:",
        'choose_id_type': "Choose the ID type to generate:",
        'send_error': "❌ Send error:",
        'timeout_error': "⏰ Request timeout. The operation took too long. Please try again or start a new session.",
        'generation_error': "❌ Error generating ID cards:",
        'name_amharic': "Name (Amharic)",
        'name_english': "Name (English)",
        'fin': "FIN",
        'fan_fcn': "FAN (FCN)",
        'gender_amharic': "Gender (Amharic)",
        'gender_english': "Gender (English)",
        'nationality_amharic': "Nationality (Amharic)",
        'nationality_english': "Nationality (English)",
        'phone': "Phone",
        'dob_amharic': "DOB (Amharic)",
        'dob_english': "DOB (English)",
        'region_amharic': "Region (Amharic)",
        'region_english': "Region (English)",
        'subcity_amharic': "Sub City (Amharic)",
        'subcity_english': "Sub City (English)",
        'woreda_amharic': "Woreda (Amharic)",
        'woreda_english': "Woreda (English)",
        'address_amharic': "Amharic",
        'address_english': "English",
        'issue_date': "Issue Date",
        'expiry_date': "Expiry Date",
        'not_found': "Not found",
        'cleaned_fin': "✨ **Cleaned FIN:** `{fin}`\n\n",
        'your_fin': "📋 **Your FIN:** `{fin}`\n",
        'fin_label': "📋 **FIN:** `{fin}`\n\n",
        'extracted_data_preview': "📋 **Extracted Data Preview**\n\n",
        'personal_information': "👤 **Personal Information:**",
        'date_of_birth': "📅 **Date of Birth:**",
        'address_information': "📍 **Address Information:**",
        'combined_address': "🏠 **Combined Address:**",
        'card_dates': "📆 **Card Dates:**",
        'what_would_you_like': "💡 **What would you like to do?**\n\n",
        'data_correct': "✅ **If the data looks correct:** Proceed to generation options\n",
        'need_to_edit': "✏️ **If you need to edit:** Review and modify specific fields\n"
    },
    'am': {
        'welcome': "🇪🇹 *የኢትዮጵያ ዲጂታል መለያ ቦት እንኳን ደህና መጡ*\n\nሰላም {name}!\n\n**እንዴት እንደሚሰራ:**\n📄 PDF ይላኩ → 🔢 FIN ይላኩ → 🎯 መለያዎን ያገኙ\n\n**ሁለት ሁነታዎች አሉ:**\n• **ዝርዝር ሁነታ**: ሁሉንም ቅንብሮች ቁጥጥር\n• **ነባሪ ሁነታ**: በራስ-ሰር በብቃት ይፍጠር\n\n**ቅንብሮችን ለማዋቀር ቅንብሮችን ይንኩ:**",
        'help': "🇪🇹 *እርዳታ*\n\nቦቱን በሶስት ደረጃዎች ይጠቀሙ:\n1) PDF ይላኩ\n2) 12-አሃዝ FIN ይላኩ\n3) ይገምግሙ እና መለያዎን ይፍጠሩ\n\nትዕዛዞች:\n/help — እርዳታ\n/cancel — ክፍለ-ጊዜ ይሰርዙ\n/compress — ትልቅ PDF ይጨምሩ\n/report — ዕለታዊ ሪፖርት ያግኙ\n\nምክር: ማንኛውንም መልዕክት በመላክ መጀመር ይችላሉ።",
        'pdf_uploaded': "✅ PDF በተሳካ ሁኔታ ተላከ። እባክዎ 12-አሃዝ FIN ቁጥርዎን ይላኩ።",
        'settings': "⚙️ **ቅንብሮች**\n\n• የጠርዝ ማስወገጃ: `{bg}`\n• የመለያ አይነት: `{id_type}`\n• የውጤት ልዩነት: `{variant}`\n• የአድራሻ ቅርጸት: `{city}`\n• ሁነታ: `{mode}`\n• ቋንቋ: `{language}`\n\nለመቀየር ይንኩ:",
        'settings_prompt': "🔧 **የመለያ ማመንጫ ቅንብሮች**\n\nየጠርዝ ማስወገጃ፣ የመለያ አይነት፣ የውጤት ቅርጸት እና ሌሎች ቅንብሮችን መስራት ይችላሉ። መለያዎን ከመፍጠር በፊት ምርጫዎን ይምረጡ።",
        'bg_options': "**የጠርዝ ማስወገጃ አማራጮች:**\n\nከመለያ ፎቶዎ ምን አይነት ጠርዝ እንደሚወገድ ይምረጡ:",
        'id_type_options': "**የመለያ አይነት አማራጮች:**\n\nምን አይነት መለያ እንደሚፈጥር ይምረጡ:",
        'variant_options': "**የውጤት ልዩነት አማራጮች:**\n\nለመለያዎ የቀለም ዘይቤ ይምረጡ:",
        'city_options': "**የአድራሻ ቅርጸት አማራጮች:**\n\nየአድራሻ ቅርጸትዎን (የከተማ አይነት) ይምረጡ:",
        'mode_options': "**ሁነታ አማራጮች:**\n\nምን አይነት ሁነታ እንደሚፈልጉ ይምረጡ:",
        'lang_options': "**ቋንቋ አማራጮች:**\n\nምን አይነት ቋንቋ እንደሚፈልጉ ይምረጡ:",
        'ready_start': "📄 **ለመጀመር ዝግጁ!**\n\nእባክዎ ይፋዊ PDF ሰነድዎን ይላኩ።",
        'mode_detail': "ዝርዝር ሁነታ",
        'mode_default': "ነባሪ ሁነታ",
        'lang_english': "English", 
        'lang_amharic': "አማርኛ",
        'back': "🔙 ተመለስ",
        'close': "❌ ዝጋ",
        'access_denied': "🚫 **መዳረሻ ተከልክሏል**\n\nይቅርታ፣ ይህን ቦት ለመጠቀም አልተፈቀደልዎትም።\n\nይህ ቦት ለተፈቅደላቸው ተጠቃሚዎች ብቻ የተገደበ ነው። መዳረሻ ማግኘት ከፈለጉ፣ ከአስተዳዳሪዎች ጋር መነጋገር አለብዎት።\n\nለመዳረሻ፣ ከአስተዳዳሪ ጋር ይገናኙ፡\n\n{safe_admin}\n\nለመረዳትዎ እናመሰግናለን።",
        'bot_paused': "⏸️ ቦቱ በአስተዳዳሪ ተቆጥቷል።\n\n📊 ቦቱ እንደገና እንዲጀመር እባክዎ ይጠብቁ።\n\nለእርዳታ፣ ከ @fayda\\_software ጋር ይገናኙ",
        'account_paused': "⏸️ ሂሳብዎ በአስተዳዳሪ ተቆጥቷል። እባክዎ ለእርዳታ ከ @fayda\\_software ጋር ይገናኙ።",
        'welcome_fallback': "እንኳን ደህና መጡ! እባክዎ በመጀመሪያ ይፋዊ PDF ሰነድዎን ይላኩ።",
        'error_generating_report': "ሪፖርት ማመንጫ ላይ ስህተት:",
        'downloading_pdf': "🌐 PDF ከአገናኙ እየሰረዝ ነው... እባክዎ ይጠብቁ።",
        'processing_pdf': "⏳ ከ PDF ውስጥ ውሂብ እየሰራ ነው...",
        'daily_report_no_ids': "📊 **ዕለታዊ ሪፖርት - {date}**\n\n👤 ተጠቃሚ: {username}\n📈 ዛሬ የተፈጠሩ መለያዎች: 0\n📈 አጠቃላይ የተፈጠሩ መለያዎች: {total_count}\n💰 የሚከፈል: 0 ብር\n\nአገልግሎታችንን ስለጠቀሙ እናመሰግናለን! 🙏",
        'daily_report_with_ids': "📊 **ዕለታዊ ሪፖርት - {date}**\n\n👤 ተጠቃሚ: {username}\n📈 ዛሬ የተፈጠሩ መለያዎች: {today_count}\n📈 አጠቃላይ የተፈጠሩ መለያዎች: {total_count}\n💰 የሚከፈል: {payment_due} ብር\n\n💳 እባክዎ ክፍያዎን ያጠናቅቁ እና ስክሪንሾትን ለአስተዳዳሪ @fayda\\_software ያስገቡ\n\nአገልግሎታችንን ስለጠቀሙ እናመሰግናለን! 🙏",
        'access_granted': "🎉 **መዳረሻ ተፈቅዷል!**\n\n✅ ዛሬ የተፈጠሩ መለያዎች: {today_count}\n📈 አጠቃላይ ያልተከፈሉ መለያዎች: {total_unpaid}",
        'id_ready': "🎉 መለያዎ ዝግጁ ነው! አዲስ ክፍለ-ጊዜ ለመጀመር ማንኛውንም መልዕክት ይላኩ።",
        'access_denied_short': "🚫 **መዳረሻ ተከልክሏል**\n\nይህን ቦት ለመጠቀም አልተፈቀደልዎትም።\nከአስተዳዳሪ ጋር ለመዳረሻ ይገናኙ።\n\nየእርስዎ የተጠቃሚ መለያ: `{user_id}`",
        'access_revoked': "🚫 **መዳረሻ ተመለሰ**\n\nየቦቱ መዳረሻዎ በአስተዳዳሪ ተመለሰ።\nከአሁን በኋላ መለያ ለመፍጠር ቦቱን መጠቀም አይችሉም።\n\nይህ ስህተት ነው ብለው ካሰቡ፣ እባክዎ ከአስተዳዳሪ ጋር ይገናኙ።\nከአስተዳዳሪ ጋር ይገናኙ፡\n\n@fayda\\_software\n\nለመረዳትዎ እናመሰግናለን።",
        'processing_id': "🔄 **መለያዎችዎን እየሰራ ነው...**\n\n⏳ ይህ ጥቂት ጊዜ ሊወስድ ይችላል።\n📱 ምስሎችዎን እየፈጠርኩ እንደሆነ እባክዎ ይጠብቁ...",
        'photo_sent': "ፎቶ ተላከ። መተካት ወይም መቀጠል ይችላሉ።",
        'choose_background': "የጠርዝ ማስወገጃ አማራጮችዎን ይምረጡ:",
        'choose_id_type': "ለመፍጠር የመለያ አይነት ይምረጡ:",
        'send_error': "❌ የመላክ ስህተት:",
        'timeout_error': "⏰ የጥያቄ ጊዜ አልፏል። ክወናው በጣም ረጅም ቆይቷል። እባክዎ እንደገና ይሞክሩ ወይም አዲስ ክፍለ-ጊዜ ይጀምሩ።",
        'generation_error': "❌ የመለያ ማመንጫ ስህተት:",
        'name_amharic': "ስም (አማርኛ)",
        'name_english': "ስም (እንግሊዝኛ)",
        'fin': "FIN",
        'fan_fcn': "FAN (FCN)",
        'gender_amharic': "ጾታ (አማርኛ)",
        'gender_english': "ጾታ (እንግሊዝኛ)",
        'nationality_amharic': "ዜግነት (አማርኛ)",
        'nationality_english': "ዜግነት (እንግሊዝኛ)",
        'phone': "ስልክ",
        'dob_amharic': "የትውልድ ቀን (አማርኛ)",
        'dob_english': "የትውልድ ቀን (እንግሊዝኛ)",
        'region_amharic': "ክልል (አማርኛ)",
        'region_english': "ክልል (እንግሊዝኛ)",
        'subcity_amharic': "ክፍለ ከተማ (አማርኛ)",
        'subcity_english': "ክፍለ ከተማ (እንግሊዝኛ)",
        'woreda_amharic': "ወረዳ (አማርኛ)",
        'woreda_english': "ወረዳ (እንግሊዝኛ)",
        'address_amharic': "አማርኛ",
        'address_english': "እንግሊዝኛ",
        'issue_date': "የተሰጠበት ቀን",
        'expiry_date': "የሚያልቅበት ቀን",
        'not_found': "አልተገኘም",
        'cleaned_fin': "✨ **የተሰረዘ FIN:** `{fin}`\n\n",
        'your_fin': "📋 **የእርስዎ FIN:** `{fin}`\n",
        'fin_label': "📋 **FIN:** `{fin}`\n\n",
        'extracted_data_preview': "📋 **የተወሰደ ውሂብ ቅድመ-እይታ**\n\n",
        'personal_information': "👤 **የግል መረጃ:**",
        'date_of_birth': "📅 **የትውልድ ቀን:**",
        'address_information': "📍 **የአድራሻ መረጃ:**",
        'combined_address': "🏠 **የተጣመረ አድራሻ:**",
        'card_dates': "📆 **የካርድ ቀኖች:**",
        'what_would_you_like': "💡 **ምን ማድረግ ይፈልጋሉ?**\n\n",
        'data_correct': "✅ **ውሂቡ ትክክል ከሆነ:** ወደ ማመንጫ አማራጮች ይቀጥሉ\n",
        'need_to_edit': "✏️ **ማስተካከል ካስፈለጋችሁ:** የተወሰኑ መስኮችን ይገምግሙ እና ያሻሽሉ\n"
    }
}

def get_text(user_prefs: Dict, key: str, **kwargs) -> str:
    """Get translated text based on user language preference"""
    lang = user_prefs.get('language', 'am')  # Default to Amharic
    return TRANSLATIONS.get(lang, TRANSLATIONS['am'])[key].format(**kwargs)

# Conversation states
WAITING_FOR_PDF = 1
WAITING_FOR_FIN = 2
WAITING_FOR_PHOTO = 3
CONFIRMING_DATA = 4
WAITING_FOR_LANGUAGE = 5
WAITING_FOR_FIELD_VALUE = 6
WAITING_FOR_UNAUTHORIZED_LANGUAGE = 7

EDITABLE_FIELDS = [
    'name_en', 'name_am', 'gender_en', 'gender_am', 'dob_en', 'dob_am', 'nationality_en', 'nationality_am',
    'region_en', 'region_am', 'subcity_en', 'subcity_am', 'woreda_en', 'woreda_am', 'phone'
]

ADDRESS_FIELDS = ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']
NATIONALITY_FIELDS = ['nationality_am', 'nationality_en']

CITY_TYPES = ['default', 'residential_sheger']

class FydaTelegramBot:
    def __init__(self, token: str, allowed_user_ids: List[int] = None):
        self.token = token
        self.id_service = IDCardService()
        self.daily_service = DailyReportService()
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        # List of allowed Telegram user IDs (None means all users are allowed)
        self.allowed_user_ids = allowed_user_ids or []
        # If allowed_user_ids was provided (even if empty), restrict access
        # Only allow all users if no allowlist was provided at all
        self.restrict_access = allowed_user_ids is not None
        # Admin IDs (for notifications)
        self.admin_user_ids: List[int] = []
        # Track recently notified users to prevent duplicates
        self.recently_notified: Dict[int, float] = {}
        # Ethiopia timezone
        self.ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')
        # User language preferences storage
        self.user_preferences_file = os.path.join(os.path.dirname(__file__), 'data', 'user_preferences.json')
        self.user_preferences = self._load_user_preferences()
        try:
            admin_ids_env = os.getenv('ADMIN_USER_IDS', '')
            if admin_ids_env:
                self.admin_user_ids = [int(x.strip()) for x in admin_ids_env.split(',') if x.strip()]
        except Exception:
            self.admin_user_ids = []

    def _load_user_preferences(self) -> Dict[int, Dict[str, Any]]:
        """Load user preferences from file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.user_preferences_file), exist_ok=True)
            
            if os.path.exists(self.user_preferences_file):
                with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    return {int(k): v for k, v in data.items()}
            return {}
        except Exception as e:
            print(f"⚠️ Error loading user preferences: {e}")
            return {}
    
    def _save_user_preferences(self) -> None:
        """Save user preferences to file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.user_preferences_file), exist_ok=True)
            
            # Convert integer keys to strings for JSON serialization
            data = {str(k): v for k, v in self.user_preferences.items()}
            
            with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving user preferences: {e}")
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language, default to Amharic if not set"""
        return self.user_preferences.get(user_id, {}).get('language', 'am')
    
    def set_user_language(self, user_id: int, language: str) -> None:
        """Set user's preferred language and save to file and Firebase"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id]['language'] = language
        
        # Update in session prefs if available
        if user_id in self.user_sessions:
            if 'prefs' not in self.user_sessions[user_id]:
                self.user_sessions[user_id]['prefs'] = {}
            self.user_sessions[user_id]['prefs']['language'] = language
        
        self._save_user_preferences()
        
        # Sync all preferences to Firebase (comprehensive sync)
        self._sync_preferences_to_firebase(user_id)
    
    def is_new_user(self, user_id: int) -> bool:
        """Check if this is a new user who hasn't set language preference yet"""
        return user_id not in self.user_preferences
    
    async def _create_or_update_user_in_firebase(self, user_id: int, user_name: str, username: str) -> None:
        """Create or update user data in Firebase"""
        try:
            # Get existing user data from Firebase
            existing_user = firebase_service.get_user_data(str(user_id))
            
            # Prepare user data
            user_data = {
                'telegramId': str(user_id),
                'firstName': user_name,
                'username': username,
                'lastActivity': datetime.now().isoformat() + "Z"
            }
            
            # If user exists, preserve existing data and update
            if existing_user:
                user_data.update({
                    'access_status': existing_user.get('access_status', 'not approved'),
                    'today_ids': existing_user.get('today_ids', 0),
                    'total_ids': existing_user.get('total_ids', 0),
                    'paid': existing_user.get('paid', 0),
                    'unpaid': existing_user.get('unpaid', 0),
                    'preferences': existing_user.get('preferences', {
                        'language': 'am',
                        'id_type': 'normal',
                        'output_variant': 'front_color',
                        'city_type': 'default',
                        'mode': 'default',
                        'remove_white_bg': False,
                        'remove_black_bg': False
                    })
                })
            else:
                # New user - set default values with status "not approved"
                user_data.update({
                    'access_status': 'not approved',
                    'today_ids': 0,
                    'total_ids': 0,
                    'paid': 0,
                    'unpaid': 0,
                    'preferences': {
                        'language': 'am',
                        'id_type': 'normal',
                        'output_variant': 'front_color',
                        'city_type': 'default',
                        'mode': 'default',
                        'remove_white_bg': False,
                        'remove_black_bg': False
                    }
                })
            
            # Create or update user in Firebase
            firebase_service.create_or_update_user(user_data)
            
            # Update local user preferences from Firebase data
            if 'preferences' in user_data:
                self.user_preferences[user_id] = user_data['preferences']
                self._save_user_preferences()
            
            # Also sync preferences separately to ensure consistency
            # This ensures preferences are properly saved in the users collection
            if user_id in self.user_sessions and 'prefs' in self.user_sessions[user_id]:
                self._sync_preferences_to_firebase(user_id)
            elif user_id in self.user_preferences:
                # Sync from local preferences if session doesn't have prefs yet
                try:
                    firebase_service.update_user_preferences(str(user_id), self.user_preferences[user_id])
                    print(f"✅ Synced existing preferences for user {user_id} to Firebase")
                except Exception as e:
                    print(f"⚠️ Error syncing existing preferences to Firebase: {e}")
            
        except Exception as e:
            print(f"⚠️ Error creating/updating user in Firebase: {e}")
            # Continue with local storage fallback
    
    def _sync_preferences_to_firebase(self, user_id: int) -> None:
        """Sync user preferences to Firebase - comprehensive sync of all settings"""
        try:
            # Build comprehensive preferences from session data and prefs
            prefs = {}
            
            # Get preferences from session if available
            if user_id in self.user_sessions and 'prefs' in self.user_sessions[user_id]:
                prefs.update(self.user_sessions[user_id]['prefs'])
            
            # Also get preferences from data section (settings that are in data)
            if user_id in self.user_sessions and 'data' in self.user_sessions[user_id]:
                data = self.user_sessions[user_id]['data']
                
                # Sync ID type and related settings from data to prefs
                if 'id_type' in data:
                    prefs['id_type'] = data['id_type']
                if 'output_variant' in data:
                    prefs['output_variant'] = data['output_variant']
                if 'remove_white_bg' in data:
                    prefs['remove_white_bg'] = data['remove_white_bg']
                if 'remove_black_bg' in data:
                    prefs['remove_black_bg'] = data['remove_black_bg']
                if 'city_type' in data:
                    prefs['city_type'] = data.get('city_type')
                if 'generate_old_id' in data:
                    prefs['generate_old_id'] = data['generate_old_id']
                if 'generate_mini_id' in data:
                    prefs['generate_mini_id'] = data['generate_mini_id']
            
            # If no session, try to get from local preferences
            if not prefs and user_id in self.user_preferences:
                prefs = self.user_preferences[user_id].copy()
            
            # Update Firebase if we have preferences
            if prefs:
                firebase_service.update_user_preferences(str(user_id), prefs)
                
                # Also update local storage
                self.user_preferences[user_id] = prefs
                self._save_user_preferences()
                print(f"✅ Synced preferences for user {user_id} to Firebase: {list(prefs.keys())}")
        except Exception as e:
            print(f"⚠️ Error syncing preferences to Firebase: {e}")
    
    def update_user_access_status(self, user_id: int, status: str) -> bool:
        """Update user access status in Firebase and local storage"""
        try:
            # Update in Firebase
            firebase_service.update_user_access_status(str(user_id), status)
            
            # Update local allowlist if approved
            if status == 'approved':
                if user_id not in self.allowed_user_ids:
                    self.allowed_user_ids.append(user_id)
                    self.allowed_user_ids.sort()
            elif status in ['rejected', 'paused']:
                if user_id in self.allowed_user_ids:
                    self.allowed_user_ids.remove(user_id)
            
            # Update local allowlist file
            try:
                allowlist_path = os.path.join(os.path.dirname(__file__), 'data', 'allowed_users.json')
                os.makedirs(os.path.dirname(allowlist_path), exist_ok=True)
                with open(allowlist_path, 'w', encoding='utf-8') as f:
                    json.dump(self.allowed_user_ids, f, indent=2)
            except Exception as e:
                print(f"⚠️ Error updating local allowlist: {e}")
            
            print(f"✅ Updated user {user_id} access status to {status}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user access status: {e}")
            return False

    def _city_label(self, city_key: str) -> str:
        """Return human-friendly label for city/address format."""
        if city_key == 'residential_sheger':
            return 'Sheger City Address'
        if city_key == 'default':
            return 'Default Address'
        return city_key.replace('_', ' ').title()
    
    def is_bot_paused(self) -> bool:
        """Check if the bot is manually paused by admin."""
        return self.daily_service.is_bot_paused()
    
    def get_text_for_user(self, user_prefs: Dict, key: str, **kwargs) -> str:
        """Get translated text for a specific user based on their language preference"""
        return get_text(user_prefs, key, **kwargs)
    
    def get_pause_message(self) -> str:
        """Get the pause message for users."""
        return self.get_text_for_user({'language': 'am'}, 'bot_paused')
    
    async def send_daily_report_to_user(self, user_id: int, username: str = None) -> bool:
        """Send daily report to a specific user."""
        try:
            stats = self.daily_service.get_user_stats(user_id)
            today_count = stats["today_count"]
            total_count = stats["total_generated"]
            payment_due = today_count * 50
            
            if today_count == 0:
                message = self.get_text_for_user({'language': 'am'}, 'daily_report_no_ids', 
                                                date=self.daily_service._get_today_key(),
                                                username=stats['username'],
                                                total_count=total_count)
            else:
                message = self.get_text_for_user({'language': 'am'}, 'daily_report_with_ids',
                                                date=self.daily_service._get_today_key(),
                                                username=stats['username'],
                                                today_count=today_count,
                                                total_count=total_count,
                                                payment_due=payment_due)
            
            # Send message to user
            application = Application.builder().token(self.token).build()
            await application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            return True
            
        except Exception as e:
            print(f"Error sending daily report to user {user_id}: {str(e)}")
            return False

    def _refresh_allowlist_from_file(self) -> None:
        """Load allowlist from file so updates apply at runtime."""
        try:
            # Direct file reading instead of importing allowlist_store
            allowlist_path = os.path.join(os.path.dirname(__file__), 'data', 'allowed_users.json')
            if os.path.exists(allowlist_path):
                with open(allowlist_path, 'r', encoding='utf-8') as f:
                    file_ids = json.load(f)
                if isinstance(file_ids, list):
                    # Convert to integers and filter out invalid entries
                    result = []
                    for item in file_ids:
                        try:
                            result.append(int(item))
                        except (ValueError, TypeError):
                            continue
                    self.allowed_user_ids = sorted(set(result))
                    # Always restrict access when using allowlist (even if empty)
                    self.restrict_access = True
                    print(f"🔄 Refreshed allowlist from file: {len(self.allowed_user_ids)} users")
            else:
                print("⚠️ Allowlist file not found, using current allowlist")
        except Exception as e:
            print(f"⚠️ Error refreshing allowlist from file: {e}")
            # Fail closed to current in-memory list
            pass

    def is_user_authorized(self, user_id: int) -> bool:
        """Check if a user is authorized to use the bot"""
        if not self.restrict_access:
            print(f"🔓 Access not restricted, allowing user {user_id}")
            return True
        
        # First check local file-based authorization (primary source of truth)
        self._refresh_allowlist_from_file()
        is_in_local_file = user_id in self.allowed_user_ids
        print(f"🔍 User {user_id} file authorization check: {is_in_local_file} (allowed users: {self.allowed_user_ids})")
        
        # If user is in local file, they are authorized
        if is_in_local_file:
            # Also sync to Firebase to keep it updated
            try:
                user_data = firebase_service.get_user_data(str(user_id))
                if user_data:
                    current_status = user_data.get('access_status', 'not approved')
                    if current_status != 'approved':
                        print(f"🔄 Syncing user {user_id} to Firebase as approved")
                        firebase_service.update_user_access_status(str(user_id), 'approved')
            except Exception as e:
                print(f"⚠️ Error syncing to Firebase: {e}")
            return True
        
        # If not in local file, check Firebase as fallback
        try:
            user_data = firebase_service.get_user_data(str(user_id))
            if user_data:
                access_status = user_data.get('access_status', 'not approved')
                is_authorized = access_status == 'approved'
                print(f"🔍 User {user_id} Firebase authorization check: {is_authorized} (status: {access_status})")
                return is_authorized
        except Exception as e:
            print(f"⚠️ Error checking Firebase authorization: {e}")
        
        return False

    async def _notify_admins_new_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, user_name: str, username: str) -> None:
        import time
        
        # Check if we've already notified about this user recently (within 30 seconds)
        current_time = time.time()
        if user_id in self.recently_notified:
            time_diff = current_time - self.recently_notified[user_id]
            if time_diff < 30:  # 30 seconds cooldown
                print(f"⏭️ Skipping duplicate notification for user {user_id} (notified {time_diff:.1f}s ago)")
                return
        
        # Record this notification
        self.recently_notified[user_id] = current_time
        
        # Clean up old entries (older than 5 minutes)
        cutoff_time = current_time - 300  # 5 minutes
        self.recently_notified = {uid: timestamp for uid, timestamp in self.recently_notified.items() if timestamp > cutoff_time}
        
        # Send to admin dashboard backend to appear in New Comer page
        try:
            import asyncio
            import requests
            from datetime import datetime
            payload = {
                "id": str(user_id),
                "telegramId": str(user_id),
                "username": username or "",
                "firstName": user_name,
                "lastName": "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "pending",
            }
            backend_url = os.getenv('ADMIN_BACKEND_URL', 'http://localhost:5000')
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(f"{backend_url}/api/new-users", json=payload, timeout=5)
            )
            print(f"✅ New user {user_id} ({user_name}) sent to admin dashboard")
        except Exception as e:
            print(f"❌ Error sending new user to dashboard: {e}")
            pass

    def get_unauthorized_message(self, user_id: int) -> str:
        admin_contact = os.getenv('ADMIN_CONTACT', '@fayda_software')
        # Escape underscores for Markdown to avoid entity parse errors
        safe_admin = admin_contact.replace('_', '\\_')
        user_lang = self.get_user_language(user_id)
        return self.get_text_for_user({'language': user_lang}, 'access_denied', safe_admin=safe_admin)

    def get_support_footer(self) -> str:
        # Plain footer, safe for non-Markdown messages
        return "\n\nNeed help? @fayda_software"

    def _user_static_path(self, user_id: int, base_filename: str) -> str:
        """Create a user-scoped filename to avoid collisions across users."""
        name, ext = os.path.splitext(base_filename)
        safe_name = f"{name}_{user_id}{ext}"
        return os.path.join(self.id_service.config.STATIC_FOLDER, safe_name)

    async def auto_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Auto-start the bot when user sends any message (not just /start)"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Unknown"
        username = update.effective_user.username or ""
        
        # Check if bot is manually paused by admin
        if self.is_bot_paused():
            await update.message.reply_text(self.get_pause_message(), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Check if user is paused by admin
        if self.daily_service.is_user_paused(user_id):
            await update.message.reply_text(self.get_text_for_user({'language': 'am'}, 'account_paused'), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # First, create or update user in Firebase (this ensures all users exist in Firebase with their status)
        await self._create_or_update_user_in_firebase(user_id, user_name, username)
        
        # Check if user is authorized (this checks Firebase status)
        if not self.is_user_authorized(user_id):
            # Notify admins about the new/unauthorized user trying to start
            await self._notify_admins_new_user(
                context,
                user_id,
                update.effective_user.first_name or "Unknown",
                update.effective_user.username or ""
            )
            
            # Check if this is a new user who hasn't set language preference
            if self.is_new_user(user_id):
                # Ask for language selection first before showing access denied message
                language_text = (
                    "� **Wlelcome! Please select your preferred language:**\n\n"
                    "🇪🇹 **አማርኛ** - Amharic (Default)\n"
                    "🇺🇸 **English** - English\n\n"
                    "Choose your language to continue:"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="unauthorized_lang_am")],
                    [InlineKeyboardButton("🇺🇸 English", callback_data="unauthorized_lang_en")]
                ]
                
                await update.message.reply_text(
                    language_text, 
                    parse_mode=ParseMode.MARKDOWN, 
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return WAITING_FOR_UNAUTHORIZED_LANGUAGE
            else:
                # User has already set language preference, show access denied in their language
                await update.message.reply_text(self.get_unauthorized_message(user_id), parse_mode=ParseMode.MARKDOWN)
                return ConversationHandler.END
        
        # Check if this is a new user (no existing session)
        is_new_user = user_id not in self.user_sessions
        
        # Check if user needs to set language preference (first time user)
        if self.is_new_user(user_id):
            language_text = (
                "🌍 **Welcome! Please select your preferred language:**\n\n"
                "🇪🇹 **አማርኛ** - Amharic (Default)\n"
                "🇺🇸 **English** - English\n\n"
                "Choose your language to continue:"
            )
            
            keyboard = [
                [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")],
                [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
            ]
            
            await update.message.reply_text(
                language_text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_LANGUAGE
        
        # Initialize user session; preserve existing preferences across restarts
        user_lang = self.get_user_language(user_id)
        
        # Load preferences from Firebase if available
        try:
            firebase_user_data = firebase_service.get_user_data(str(user_id))
            if firebase_user_data and 'preferences' in firebase_user_data:
                firebase_prefs = firebase_user_data['preferences']
                # Update local preferences from Firebase
                self.user_preferences[user_id] = firebase_prefs
                self._save_user_preferences()
                # Use Firebase preferences as base
                preserved_prefs = firebase_prefs.copy()
                # Ensure language is set
                if 'language' not in preserved_prefs:
                    preserved_prefs['language'] = user_lang
                else:
                    user_lang = preserved_prefs['language']
            else:
                # Fallback to session or default preferences
                preserved_prefs = self.user_sessions.get(user_id, {}).get('prefs', {
                    'id_type': None,
                    'output_variant': None,
                    'city_type': None,
                    'mode': 'default',
                    'language': user_lang,
                })
        except Exception as e:
            print(f"⚠️ Error loading preferences from Firebase: {e}")
            # Fallback to session or default preferences
        preserved_prefs = self.user_sessions.get(user_id, {}).get('prefs', {
            'id_type': None,
            'output_variant': None,
            'city_type': None,
            'mode': 'default',
            'language': user_lang,
        })
        # Initialize data with preserved settings from prefs
        initial_data = {}
        if 'id_type' in preserved_prefs and preserved_prefs['id_type']:
            initial_data['id_type'] = preserved_prefs['id_type']
        if 'remove_white_bg' in preserved_prefs:
            initial_data['remove_white_bg'] = preserved_prefs.get('remove_white_bg', False)
        if 'remove_black_bg' in preserved_prefs:
            initial_data['remove_black_bg'] = preserved_prefs.get('remove_black_bg', False)
        if 'output_variant' in preserved_prefs and preserved_prefs['output_variant']:
            initial_data['output_variant'] = preserved_prefs['output_variant']
        if 'city_type' in preserved_prefs and preserved_prefs['city_type']:
            initial_data['city_type'] = preserved_prefs['city_type']
        if 'generate_old_id' in preserved_prefs:
            initial_data['generate_old_id'] = preserved_prefs.get('generate_old_id', False)
        if 'generate_mini_id' in preserved_prefs:
            initial_data['generate_mini_id'] = preserved_prefs.get('generate_mini_id', False)
            
        self.user_sessions[user_id] = {
            'data': initial_data, 
            'files': {}, 
            'edit_field': None,
            'edit_mode': None,
            'current_edit_index': 0,
            'prefs': preserved_prefs,
            'preview_visible': False,
            'preview_message_id': None
        }
        
        # Sync preferences to Firebase when session is initialized (if preferences exist)
        if preserved_prefs:
            try:
                # Sync all preferences to Firebase
                self._sync_preferences_to_firebase(user_id)
            except Exception as e:
                print(f"⚠️ Error syncing preferences on session init: {e}")
        
        # If this is a new user, ask for language selection first
        if is_new_user:
            language_text = (
                "🌍 **Welcome! Please select your preferred language:**\n\n"
                "🇪🇹 **አማርኛ** - Amharic (Default)\n"
                "🇺🇸 **English** - English\n\n"
                "Choose your language to continue:"
            )
            
            keyboard = [
                [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")],
                [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
            ]
            
            await update.message.reply_text(
                language_text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_LANGUAGE
        
        # Get user's ID generation stats
        stats = self.daily_service.get_user_stats(user_id)
        today_count = stats["today_count"]
        total_count = stats["total_generated"]
        
        # Add ID count to welcome message
        welcome = get_text(self.user_sessions[user_id]['prefs'], 'welcome', name=user_name)
        if today_count > 0:
            welcome += f"\n\n📊 **Your Stats Today:**\n✅ IDs Generated: {today_count}\n📈 Total Unpaid Generated: {stats.get('total_unpaid', 0)}"
        
        # Add only one settings button
        keyboard = [
            [InlineKeyboardButton("⚙️ Settings", callback_data="quick_settings")]
        ]
        
        try:
            await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        except NetworkError as e:
            # Retry once after a short delay, then fall back to plain text
            try:
                import asyncio
                await asyncio.sleep(1.0)
                await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                try:
                    await update.message.reply_text(self.get_text_for_user({'language': 'am'}, 'welcome_fallback'))
                except Exception as _:
                    # Give up gracefully if network keeps failing
                    return ConversationHandler.END
        return WAITING_FOR_PDF

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the bot with /start command"""
        return await self.auto_start(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            await update.message.reply_text(self.get_unauthorized_message(user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        help_text = get_text(self.user_sessions[user_id]['prefs'], 'help')
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    async def daily_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Send daily report to user"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            await update.message.reply_text(self.get_unauthorized_message(user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        try:
            stats = self.daily_service.get_user_stats(user_id)
            today_count = stats["today_count"]
            total_unpaid = stats.get("total_unpaid", 0)
            today_unpaid = stats.get("today_unpaid", 0)
            
            if today_count == 0:
                message = f"📊 **Your Stats:**\n✅ IDs Generated Today: 0\n📈 Total Unpaid Generated: {total_unpaid}"
            else:
                message = f"📊 **Your Stats:**\n✅ IDs Generated Today: {today_count}\n📈 Total Unpaid Generated: {total_unpaid}\n\n💳 Please complete your payment and attach the screenshot for admin @fayda_software"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"{self.get_text_for_user({'language': 'am'}, 'error_generating_report')} {str(e)}")
        
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            await update.message.reply_text(self.get_unauthorized_message(user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        self.user_sessions.pop(user_id, None)
        await update.message.reply_text(
            "❌ **Session Cancelled**\n\n"
            "Your current session has been cancelled.\n\n"
            "🔄 **To start over:** Send any message or /start\n\n"
            "💡 *You can also just send your FIN number (with or without separators/letters) to begin immediately.*",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    async def receive_fin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Clean FIN number by removing spaces, underscores, hyphens, and other common separators
        fin = update.message.text.strip()
        original_fin = fin  # Keep original for display purposes
        
        # Remove common separators: spaces, underscores, hyphens, dots, commas, and letters
        fin = re.sub(r'[\s_\-.,a-zA-Z]', '', fin)
        
        # Show user what was cleaned (only if cleaning actually happened)
        if original_fin != fin:
            await update.message.reply_text(
                f"🧹 **FIN Number Cleaned**\n\n"
                f"📝 **Original input:** `{original_fin}`\n"
                f"{self.get_text_for_user({'language': 'am'}, 'cleaned_fin', fin=fin)}"
                "💡 *I automatically removed spaces, underscores, hyphens, letters, and other separators*",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Check if user sent a file instead of text
        if update.message.document or update.message.photo or update.message.video or update.message.audio:
            await update.message.reply_text(
                "❌ *Wrong Input Type*\n\n"
                "I need your **FIN number** (text), not a file.\n\n"
                "📝 **Please send your 12-digit FIN number**\n"
                "Example: `123456789012`\n\n"
                "💡 *What is a FIN number?*\n"
                "• It's a 12-digit number from your Ethiopian ID\n"
                "• It contains only numbers (0-9)\n"
                "• You can use separators like spaces, dashes, underscores, and even letters - I'll clean them automatically",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIN
        
        # Check if FIN is empty or too short
        if not fin:
            await update.message.reply_text(
                "❌ *Empty Input*\n\n"
                "Please send your 12-digit FIN number.\n\n"
                "📝 **Examples:** `123456789012` or `123 456 789 012` or `123-456-789-012` or `fin329036715680`",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIN
        
        # Check if FIN contains non-numeric characters
        if not fin.isdigit():
            await update.message.reply_text(
                "❌ *Invalid Characters*\n\n"
                "Your FIN number should contain **only numbers** (0-9).\n\n"
                "🔍 **I found:** `" + fin + "`\n"
                "❌ **Problem:** Contains letters or special characters\n\n"
                "✅ **Please send:** `123456789012` (12 digits only)",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIN
        
        # Check FIN length
        if len(fin) != 12:
            await update.message.reply_text(
                "❌ *Wrong Length*\n\n"
                "Your FIN number must be **exactly 12 digits**.\n\n"
                "🔍 **I received:** `" + fin + "`\n"
                "📏 **Length:** " + str(len(fin)) + " digits\n"
                "❌ **Required:** 12 digits\n\n"
                "✅ **Please send:** `123456789012` (exactly 12 digits)",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIN
        
        # FIN is valid
        self.user_sessions[user_id]['data']['fin'] = fin
        
        # Show confirmation of cleaned FIN if it was different from original
        if 'original_fin' in locals() and original_fin != fin:
            await update.message.reply_text(
                f"✅ **FIN Number Accepted!**\n\n"
                f"{self.get_text_for_user({'language': 'am'}, 'your_fin', fin=fin)}"
                f"💡 *Successfully cleaned from:* `{original_fin}`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Check if we have a PDF to process
        if not self.user_sessions[user_id].get('files', {}).get('pdf'):
            await update.message.reply_text(
                "❌ *No PDF Found*\n\n"
                "I need your PDF document to process your information.\n\n"
                "📄 **Please upload your official PDF document first**\n\n"
                "💡 *The flow is:* PDF → FIN → Data Review",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        # Now process the PDF with the FIN number
        try:
            await update.message.reply_text(
                "🔍 **Processing your PDF with FIN number...**\n\n"
                f"{self.get_text_for_user({'language': 'am'}, 'your_fin', fin=fin)}"
                f"📁 **PDF:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n\n"
                "⏳ Extracting data from your PDF...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Extract data from PDF
            pdf_bytes = self.user_sessions[user_id]['files']['pdf']
            extracted = self.id_service.extract_pdf_data(pdf_bytes, fin, 'auto')
            self.user_sessions[user_id]['data'].update(extracted)
            
            # Set sensible defaults only if not already set by user preferences
            current_data = self.user_sessions[user_id]['data']
            defaults = {
                'remove_white_bg': False,
                'remove_black_bg': False,
                'id_type': 'normal',
                'generate_mini_id': False,
                'generate_old_id': False,
                'output_variant': 'reverse',  # default to Normal Reverse Color
                'city_type': 'residential_sheger'
            }
            
            # Only set defaults for keys that don't already exist
            for key, default_value in defaults.items():
                if key not in current_data:
                    current_data[key] = default_value

            # Check if user is in default mode - skip review and generate directly
            if self.user_sessions[user_id]['prefs'].get('mode') == 'default':
                await update.message.reply_text(
                    "✅ **Data Extraction Complete!**\n\n"
                    "🚀 **Generating your ID in default mode...**",
                    parse_mode=ParseMode.MARKDOWN
                )
                # Generate ID directly without review
                return await self.generate_id_direct(update, context, user_id)
            else:
                # Detail mode - show review interface
                await update.message.reply_text(
                "✅ **Data Extraction Complete!**\n\n"
                "You can tap 🚀 Generate ID now, or adjust ⚙️ Settings first.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Show compact control panel (preview hidden by default)
            await self.show_compact_controls(update, context, user_id)
            return CONFIRMING_DATA
            
        except Exception as e:
            await update.message.reply_text(
                "❌ *PDF Processing Error*\n\n"
                f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
                f"{self.get_text_for_user({'language': 'am'}, 'fin_label', fin=fin)}"
                "🔧 **Error:** " + str(e) + "\n\n"
                "🔄 **Try again:** Upload a different PDF or check if the file is corrupted",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF

    async def generate_id_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        """Generate ID directly in default mode without review"""
        try:
            # Use the existing generation flow
            await self.generate_id(update, context, user_id)
            return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Generation Error**\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END

    async def handle_quick_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quick settings from welcome message"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data
        
        
        if choice == 'quick_settings':
            # Show full settings menu
            try:
                await self.show_settings_menu(update, context, user_id)
                return CONFIRMING_DATA
            except Exception as e:
                print(f"Settings error: {e}")  # Debug output
                await query.edit_message_text(
                    f"❌ **Settings Error**\n\n"
                    f"Error: {str(e)}\n\n"
                    "Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PDF
        
            return WAITING_FOR_PDF

    async def handle_wrong_input_fin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle wrong input types when waiting for FIN number"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Determine what type of file was sent
        if update.message.document:
            file_type = "document"
            file_name = update.message.document.file_name
        elif update.message.photo:
            file_type = "photo"
            file_name = "photo"
        elif update.message.video:
            file_type = "video"
            file_name = "video"
        elif update.message.audio:
            file_type = "audio"
            file_name = "audio"
        elif update.message.voice:
            file_type = "voice message"
            file_name = "voice message"
        else:
            file_type = "file"
            file_name = "file"
        
        await update.message.reply_text(
            f"❌ *Wrong Input Type*\n\n"
            f"I need your **FIN number** (text), not a {file_type}.\n\n"
            f"📝 **Please send your 12-digit FIN number**\n"
            f"Example: `123456789012`\n\n"
            f"💡 *What is a FIN number?*\n"
            f"• It's a 12-digit number from your Ethiopian ID\n"
            f"• It contains only numbers (0-9)\n"
            f"• No spaces, dashes, or other characters\n\n"
            f"🔄 **Try again:** Send your FIN number as text",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_FIN

    async def handle_wrong_input_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle wrong input types when waiting for PDF"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Determine what type of input was sent
        if update.message.text:
            input_type = "text"
            suggestion = "I need a **PDF file**, not text."
        elif update.message.photo:
            input_type = "photo"
            suggestion = "I need a **PDF document**, not a photo."
        elif update.message.video:
            input_type = "video"
            suggestion = "I need a **PDF document**, not a video."
        elif update.message.audio:
            input_type = "audio"
            suggestion = "I need a **PDF document**, not an audio file."
        elif update.message.voice:
            input_type = "voice message"
            suggestion = "I need a **PDF document**, not a voice message."
        else:
            input_type = "file"
            suggestion = "I need a **PDF document**."
        
        await update.message.reply_text(
            f"❌ *Wrong Input Type*\n\n"
            f"{suggestion}\n\n"
            f"📄 **Please upload your official PDF document**\n\n"
            f"💡 *How to upload a PDF:*\n"
            f"1. Tap the 📎 (attachment) button\n"
            f"2. Select 'File' or 'Document'\n"
            f"3. Choose your PDF file\n"
            f"4. Send it to me\n\n"
            f"⚠️ *Make sure it's a PDF file* (ends with .pdf)\n\n"
            f"🔄 **Try again:** Upload your PDF document",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_PDF

    async def receive_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Reset previous session data but preserve user preferences across uploads
        # Load preferences from Firebase first
        user_lang = self.get_user_language(user_id)
        try:
            firebase_user_data = firebase_service.get_user_data(str(user_id))
            if firebase_user_data and 'preferences' in firebase_user_data:
                firebase_prefs = firebase_user_data['preferences']
                # Update local preferences from Firebase
                self.user_preferences[user_id] = firebase_prefs
                self._save_user_preferences()
                # Use Firebase preferences as base
                preserved_prefs = firebase_prefs.copy()
                # Ensure language is set
                if 'language' not in preserved_prefs:
                    preserved_prefs['language'] = user_lang
                else:
                    user_lang = preserved_prefs['language']
            else:
                # Fallback to session or default preferences
                preserved_prefs = self.user_sessions.get(user_id, {}).get('prefs', {
                    'id_type': None,
                    'output_variant': None,
                    'city_type': None,
                    'mode': 'default',
                    'language': user_lang,
                })
        except Exception as e:
            print(f"⚠️ Error loading preferences from Firebase in receive_pdf: {e}")
            # Fallback to session or default preferences
            preserved_prefs = self.user_sessions.get(user_id, {}).get('prefs', {
                'id_type': None,
                'output_variant': None,
                'city_type': None,
                'mode': 'default',
                'language': user_lang,
            })
        
        # Initialize data with preserved settings from prefs
        initial_data = {}
        if 'id_type' in preserved_prefs and preserved_prefs['id_type']:
            initial_data['id_type'] = preserved_prefs['id_type']
        if 'remove_white_bg' in preserved_prefs:
            initial_data['remove_white_bg'] = preserved_prefs.get('remove_white_bg', False)
        if 'remove_black_bg' in preserved_prefs:
            initial_data['remove_black_bg'] = preserved_prefs.get('remove_black_bg', False)
        if 'output_variant' in preserved_prefs and preserved_prefs['output_variant']:
            initial_data['output_variant'] = preserved_prefs['output_variant']
        if 'city_type' in preserved_prefs and preserved_prefs['city_type']:
            initial_data['city_type'] = preserved_prefs['city_type']
        if 'generate_old_id' in preserved_prefs:
            initial_data['generate_old_id'] = preserved_prefs.get('generate_old_id', False)
        if 'generate_mini_id' in preserved_prefs:
            initial_data['generate_mini_id'] = preserved_prefs.get('generate_mini_id', False)
            
        self.user_sessions[user_id] = {
            'data': initial_data,
            'files': {},
            'edit_field': None,
            'edit_mode': None,
            'current_edit_index': 0,
            'prefs': preserved_prefs,
            'preview_visible': False,
            'preview_message_id': None
        }
        
        # Sync preferences to Firebase when session is initialized (if preferences exist)
        if preserved_prefs:
            try:
                # Sync all preferences to Firebase
                self._sync_preferences_to_firebase(user_id)
            except Exception as e:
                print(f"⚠️ Error syncing preferences on receive_pdf init: {e}")

        # If user sent text: allow direct PDF URL, otherwise guide to upload
        if update.message.text:
            text = update.message.text.strip()
            # If this looks like a direct PDF URL, let later URL handler process it
            if re.match(r"^(https?://\S+\.pdf)(\?.*)?$", text, re.IGNORECASE):
                pass
            else:
                await update.message.reply_text(
                    "❌ *Wrong Input Type*\n\n"
                    "I need a **PDF file**, not text.\n\n"
                    "📄 **Please upload your official PDF document**\n\n"
                    "💡 *Alternatively:* Send a direct link to your PDF (URL ending with .pdf)\n\n"
                    "💡 *How to get PDF links:*\n"
                    "• **Google Drive:** Upload PDF → Right-click → 'Get link' → Copy\n"
                    "• **Dropbox:** Upload PDF → Right-click → 'Copy link' → Paste\n"
                    "• **OneDrive:** Upload PDF → Right-click → 'Copy link' → Paste\n"
                    "• **Website:** If PDF is on a website, copy the full URL\n\n"
                    "💡 *How to upload a PDF:*\n"
                    "1. Tap the 📎 (attachment) button\n"
                    "2. Select 'File' or 'Document'\n"
                    "3. Choose your PDF file\n"
                    "4. Send it to me\n\n"
                    "⚠️ *Make sure it's a PDF file* (ends with .pdf)",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PDF
        
        # Check if user sent a photo instead of PDF
        if update.message.photo:
            await update.message.reply_text(
                "❌ *Wrong File Type*\n\n"
                "I need a **PDF document**, not a photo.\n\n"
                "📄 **Please upload your official PDF document**\n\n"
                "💡 *What I need:*\n"
                "• PDF file (.pdf extension)\n"
                "• Official Ethiopian ID document\n"
                "• Contains your personal information\n\n"
                "📱 *How to upload:*\n"
                "1. Tap 📎 (attachment)\n"
                "2. Select 'File' or 'Document'\n"
                "3. Choose your PDF\n"
                "4. Send it",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        # Check if user sent other file types
        if update.message.video or update.message.audio or update.message.voice:
            await update.message.reply_text(
                "❌ *Wrong File Type*\n\n"
                "I need a **PDF document**, not a video or audio file.\n\n"
                "📄 **Please upload your official PDF document**\n\n"
                "✅ **Accepted:** PDF files (.pdf)\n"
                "❌ **Not accepted:** Videos, audio, images, etc.\n\n"
                "💡 *How to upload:*\n"
                "1. Tap 📎 (attachment)\n"
                "2. Select 'File' or 'Document'\n"
                "3. Choose your PDF\n"
                "4. Send it",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        # Check if document exists and is PDF
        if not update.message.document:
            await update.message.reply_text(
                "❌ *No File Received*\n\n"
                "I didn't receive any file from you.\n\n"
                "📄 **Please upload your official PDF document**\n\n"
                "💡 *How to upload:*\n"
                "1. Tap 📎 (attachment)\n"
                "2. Select 'File' or 'Document'\n"
                "3. Choose your PDF\n"
                "4. Send it",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        # Support direct PDF URL input while waiting for PDF
        if update.message.text:
            text = update.message.text.strip()
            url_match = re.match(r"^(https?://\S+\.pdf)(\?.*)?$", text, re.IGNORECASE)
            if url_match:
                url = url_match.group(1)
                try:
                    await update.message.reply_text(self.get_text_for_user({'language': 'am'}, 'downloading_pdf'))
                    resp = requests.get(url, timeout=30)
                    resp.raise_for_status()
                    pdf_bytes = resp.content
                    # Basic size guard: up to ~25MB
                    if len(pdf_bytes) > 25 * 1024 * 1024:
                        await update.message.reply_text(
                            "❌ *File Too Large*\n\n"
                            f"📏 **Size:** {len(pdf_bytes) / (1024*1024):.1f} MB\n"
                            "❌ **Limit:** 25 MB maximum\n\n"
                            "🔄 **Try again:** Provide a smaller PDF URL",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return WAITING_FOR_PDF
                    self.user_sessions[user_id]['files']['pdf'] = pdf_bytes
                    # Immediate visual feedback
                    try:
                        await update.message.reply_text(self.get_text_for_user({'language': 'am'}, 'processing_pdf'))
                    except Exception:
                        pass
                    # Skip echoing the PDF back; just show a concise instruction message
                    # Store PDF filename for later use
                    self.user_sessions[user_id]['pdf_filename'] = 'uploaded_from_url.pdf'
                    
                    # Success message (concise)
                    prefs = self.user_sessions[user_id].get('prefs', {'language': 'am'})
                    await update.message.reply_text(
                        get_text(prefs, 'pdf_uploaded')
                    )
                    
                    return WAITING_FOR_FIN
                except Exception as e:
                    await update.message.reply_text(
                        "❌ *PDF Download/Processing Error*\n\n"
                        f"**Error:** `{str(e)}`\n\n"
                        "🔄 **Try again:** Send a valid PDF URL or upload a PDF",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_PDF

        # Check file extension
        file_name = update.message.document.file_name.lower()
        if not file_name.endswith('.pdf'):
            await update.message.reply_text(
                "❌ *Wrong File Format*\n\n"
                f"📁 **File received:** `{update.message.document.file_name}`\n"
                "❌ **Problem:** Not a PDF file\n\n"
                "📄 **I need:** A PDF document (.pdf)\n\n"
                "💡 *Please upload:*\n"
                "• Your official Ethiopian ID PDF\n"
                "• File ending with .pdf\n"
                "• Contains your personal information\n\n"
                "🔄 **Try again:** Upload the correct PDF file",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        # Check file size (limit to 25MB)
        file_size = update.message.document.file_size
        if file_size and file_size > 25 * 1024 * 1024:  # 25MB
            await update.message.reply_text(
                "❌ *File Too Large*\n\n"
                f"📁 **File:** `{update.message.document.file_name}`\n"
                f"📏 **Size:** {file_size / (1024*1024):.1f} MB\n"
                "❌ **Limit:** 25 MB maximum\n\n"
                "💡 *Solutions:*\n"
                "• **Compress PDF:** I can compress it for you\n"
                "• **Send PDF Link:** Paste a direct URL to your PDF\n"
                "• **Reduce Quality:** Use a smaller PDF version\n\n"
                "🔄 **Try again:** Upload a smaller PDF or send a link",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        
        try:
            # Immediate visual feedback
            try:
                await update.message.reply_text("⏳ Processing data from your PDF...")
            except Exception:
                pass

            # Download the PDF file
            file = await context.bot.get_file(update.message.document.file_id)
            pdf_bytes = await file.download_as_bytearray()
            self.user_sessions[user_id]['files']['pdf'] = pdf_bytes
            # Store file_id for potential reuse
            self.user_sessions[user_id]['files']['pdf_file_id'] = update.message.document.file_id

            # Do not echo the PDF back; keep UX concise


            # Store PDF filename for later use
            self.user_sessions[user_id]['pdf_filename'] = update.message.document.file_name
            
            # Success message (concise with state hint)
            prefs = self.user_sessions[user_id].get('prefs', {'language': 'en'})
            await update.message.reply_text(
                get_text(prefs, 'pdf_uploaded')
            )
            
            return WAITING_FOR_FIN
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific "File is too big" error
            if "File is too big" in error_msg or "too big" in error_msg.lower():
                # Try to automatically compress the PDF
                try:
                    await update.message.reply_text(
                        "🔄 **Large PDF Detected - Attempting Auto-Compression...**\n\n"
                        f"📁 **File:** `{update.message.document.file_name}`\n"
                        f"📏 **Size:** {file_size / (1024*1024):.1f} MB\n\n"
                        "⏳ Compressing your PDF to reduce size...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Compress the PDF
                    compressed_bytes = await self._compress_pdf_bytes(pdf_bytes)
                    compressed_size = len(compressed_bytes)
                    
                    if compressed_size < file_size:
                        # Update session with compressed PDF
                        self.user_sessions[user_id]['files']['pdf'] = compressed_bytes
                        
                        # Send compressed PDF
                        bio = BytesIO(compressed_bytes)
                        bio.name = f"compressed_{update.message.document.file_name}"
                        
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=InputFile(bio, filename=bio.name),
                            caption=(
                                f"✅ **PDF Auto-Compressed Successfully!**\n\n"
                                f"📏 **Original:** {file_size / (1024*1024):.1f} MB\n"
                                f"📏 **Compressed:** {compressed_size / (1024*1024):.1f} MB\n"
                                f"📊 **Reduction:** {((file_size - compressed_size) / file_size * 100):.1f}%\n\n"
                                f"🔄 **Now processing the compressed version...**"
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Try to process the compressed version
                        try:
                            extracted = self.id_service.extract_pdf_data(compressed_bytes, self.user_sessions[user_id]['data']['fin'], 'auto')
                            self.user_sessions[user_id]['data'].update(extracted)
                            
                            await update.message.reply_text(
                                "✅ **Compressed PDF Processed Successfully!**\n\n"
                                "📋 **Next Step:** Review your extracted data",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            
                            await self.show_compact_controls(update, context, user_id)
                            return CONFIRMING_DATA
                            
                        except Exception as comp_error:
                            await update.message.reply_text(
                                "❌ *Compressed PDF Still Too Large*\n\n"
                                "Even after compression, the file is still too big to process.\n\n"
                                "💡 *Solutions:*\n"
                                "• **Send PDF Link:** Upload to Google Drive/Dropbox and send the link\n"
                                "• **Manual Compression:** Use online PDF compressors\n"
                                "• **Reduce Quality:** Use a smaller PDF version\n\n"
                                "🔄 **Try again:** Send a link or smaller file",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return WAITING_FOR_PDF
                    
                except Exception as comp_error:
                    await update.message.reply_text(
                        "❌ *Auto-Compression Failed*\n\n"
                        f"📁 **File:** `{update.message.document.file_name}`\n"
                        f"📏 **Size:** {file_size / (1024*1024):.1f} MB\n\n"
                        "💡 *Solutions (in order of recommendation):*\n\n"
                        "1️⃣ **📎 Send PDF Link (Best Option):**\n"
                        "   • Upload to Google Drive\n"
                        "   • Right-click → 'Get link' → Copy\n"
                        "   • Send the link to me\n\n"
                        "2️⃣ **🗜️ Manual Compression:**\n"
                        "   • Use SmallPDF.com (free)\n"
                        "   • Use ILovePDF.com (free)\n"
                        "   • Target: Reduce to <15MB\n\n"
                        "3️⃣ **📱 Split PDF:**\n"
                        "   • Split into 2-3 smaller files\n"
                        "   • Send the first part\n\n"
                        "🔄 **Try again:** Send a link or compressed file",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_PDF
            
            # Handle other errors
            await update.message.reply_text(
                "❌ *PDF Processing Error*\n\n"
                "I couldn't process your PDF file.\n\n"
                "🔍 **Possible issues:**\n"
                "• File is corrupted\n"
                "• File is password protected\n"
                "• File doesn't contain readable text\n"
                "• File format is not supported\n\n"
                "💡 *Try again:*\n"
                "• Upload a different PDF file\n"
                "• Make sure it's not password protected\n"
                "• Ensure it contains your personal information\n\n"
                f"🔧 **Technical error:** {error_msg}",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF

    async def show_data_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Show a preview of extracted data for user review"""
        data = self.user_sessions[user_id]['data']
        
        # Create a comprehensive data preview
        preview_text = self.get_text_for_user({'language': 'am'}, 'extracted_data_preview')
        
        # Personal Information
        preview_text += self.get_text_for_user({'language': 'am'}, 'personal_information') + "\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'name_amharic')}:** `{data.get('name_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'name_english')}:** `{data.get('name_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'fin')}:** `{data.get('fin', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'fan_fcn')}:** `{data.get('fcn_full', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'gender_amharic')}:** `{data.get('gender_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'gender_english')}:** `{data.get('gender_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'nationality_amharic')}:** `{data.get('nationality_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'nationality_english')}:** `{data.get('nationality_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'phone')}:** `{data.get('phone', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n\n"
        
        # Date of Birth
        preview_text += self.get_text_for_user({'language': 'am'}, 'date_of_birth') + "\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'dob_amharic')}:** `{data.get('dob_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'dob_english')}:** `{data.get('dob_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n\n"
        
        # Address Information
        preview_text += self.get_text_for_user({'language': 'am'}, 'address_information') + "\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'region_amharic')}:** `{data.get('region_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'region_english')}:** `{data.get('region_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'subcity_amharic')}:** `{data.get('subcity_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'subcity_english')}:** `{data.get('subcity_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'woreda_amharic')}:** `{data.get('woreda_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
        preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'woreda_english')}:** `{data.get('woreda_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n\n"
        
        # Combined Address
        if data.get('address_am') or data.get('address_en'):
            preview_text += self.get_text_for_user({'language': 'am'}, 'combined_address') + "\n"
            preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'address_amharic')}:** `{data.get('address_am', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
            preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'address_english')}:** `{data.get('address_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n\n"
        
        # Issue/Expiry Dates (if available)
        if data.get('issue_date_en') or data.get('expiry_date_en'):
            preview_text += self.get_text_for_user({'language': 'am'}, 'card_dates') + "\n"
            preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'issue_date')}:** `{data.get('issue_date_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n"
            preview_text += f"• **{self.get_text_for_user({'language': 'am'}, 'expiry_date')}:** `{data.get('expiry_date_en', self.get_text_for_user({'language': 'am'}, 'not_found'))}`\n\n"
        
        preview_text += "---\n\n"
        preview_text += self.get_text_for_user({'language': 'am'}, 'what_would_you_like')
        preview_text += self.get_text_for_user({'language': 'am'}, 'data_correct')
        preview_text += self.get_text_for_user({'language': 'am'}, 'need_to_edit')
        preview_text += "🔄 **If data is wrong:** Upload a different PDF\n\n"
        preview_text += "⚠️ **Note:** You can edit any field after confirming the data."
        
        # Create keyboard with options
        keyboard = [
            [
                InlineKeyboardButton("✅ Data Looks Good", callback_data="data_confirm"),
                InlineKeyboardButton("✏️ Edit Data", callback_data="data_edit")
            ],
            [
                InlineKeyboardButton("🔄 Upload Different PDF", callback_data="data_retry_pdf"),
                InlineKeyboardButton("❌ Cancel", callback_data="data_cancel")
            ],
            [InlineKeyboardButton("🔁 Replace Photo", callback_data="photo_replace")]
        ]
        
        await update.message.reply_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

        # Additionally display photo, QR, and barcode as documents for preview if available
        try:
            # Photo preview
            photo_path = data.get('photo')
            if photo_path:
                abs_photo_path = os.path.join(self.id_service.config.STATIC_FOLDER, os.path.basename(photo_path))
                if os.path.exists(abs_photo_path):
                    with open(abs_photo_path, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=InputFile(f, filename='photo.png'),
                            caption='Photo preview'
                        )

            # QR preview
            qr_path = data.get('qr_path')
            if qr_path:
                abs_qr_path = os.path.join(self.id_service.config.STATIC_FOLDER, os.path.basename(qr_path))
                if os.path.exists(abs_qr_path):
                    with open(abs_qr_path, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=InputFile(f, filename='qr_code.png'),
                            caption='QR code preview'
                        )

            # Barcode preview
            if data.get('fcn_barcode'):
                barcode_path = os.path.join(self.id_service.config.STATIC_FOLDER, data['fcn_barcode'])
                if os.path.exists(barcode_path):
                    with open(barcode_path, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=InputFile(f, filename='barcode.png'),
                            caption='Barcode preview'
                        )
        except Exception as _:
            # Non-fatal: continue even if previews fail
            pass

    async def handle_photo_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        choice = query.data
        
        if choice == "photo_pdf":
            await query.edit_message_text("✅ Using photo from PDF. Now let's configure your ID generation options.")
            return await self.show_generation_options(update, context, user_id)
        elif choice == "photo_custom":
            await query.edit_message_text(
                "📸 **Upload Your Custom Photo**\n\n"
                "Please send me a clear photo of your face.\n\n"
                "💡 **Tips for best results:**\n"
                "• Take a clear, well-lit photo\n"
                "• Face should be clearly visible\n"
                "• Use a neutral background\n"
                "• Avoid shadows on your face",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO
        elif choice == "photo_download":
            # Send the currently stored photo as a downloadable document
            try:
                # Prefer the saved file in static folder (user-scoped)
                photo_path = self._user_static_path(user_id, 'photo_temp.png')
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=InputFile(f, filename='current_photo.png'),
                            caption='Current photo'
                        )
                elif self.user_sessions.get(user_id, {}).get('files', {}).get('custom_photo'):
                    from io import BytesIO
                    bio = BytesIO(self.user_sessions[user_id]['files']['custom_photo'])
                    bio.name = 'current_photo.png'
                    await context.bot.send_document(chat_id=user_id, document=bio, caption='Current photo')
            except Exception:
                pass
            # Stay in confirming state
            await context.bot.send_message(chat_id=user_id, text=self.get_text_for_user({'language': 'am'}, 'photo_sent'))
            return CONFIRMING_DATA
        elif choice == "photo_replace":
            await query.edit_message_text(
                "📸 Send a new photo to replace the current one.",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO
        else:
            await query.edit_message_text("❌ Invalid choice. Please try again.")
            return WAITING_FOR_PHOTO

    async def handle_data_preview_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user choice from data preview"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        choice = query.data

        if choice == "data_continue":
            await query.edit_message_text("➡️ Continuing to options...")
            # Background removal first
            return await self.show_background_options(update, context, user_id)

        elif choice == "data_hide":
            # Replace with compact controls (preview hidden)
            await self.show_compact_controls(update, context, user_id, replace=True)
            return CONFIRMING_DATA

        elif choice == "data_unhide":
            # Show the full data preview again
            await self.show_data_review(update, context, user_id)
            return CONFIRMING_DATA

        elif choice == "data_cancel":
            # User wants to cancel the process
            await query.edit_message_text(
                "❌ **Process Cancelled**\n\n"
                "Your ID generation process has been cancelled.\n\n"
                "🔄 **To start over:** Send any message or /start\n\n"
                "💡 *You can also just send your FIN number to begin immediately.*",
                parse_mode=ParseMode.MARKDOWN
            )
            # Clear user session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            return ConversationHandler.END
        
        elif choice == "photo_replace":
            await query.edit_message_text("📸 Send a new photo to replace the current one.", parse_mode=ParseMode.MARKDOWN)
            return WAITING_FOR_PHOTO

        elif choice == "edit_personal":
            await self.show_data_review(update, context, user_id)
            return CONFIRMING_DATA

        else:
            await query.edit_message_text("❌ Invalid choice. Please try again.")
            return CONFIRMING_DATA

    async def receive_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return WAITING_FOR_PHOTO
        
        # Check if user sent text instead of photo
        if update.message.text:
            await update.message.reply_text(
                "❌ *Wrong Input Type*\n\n"
                "I need a **photo**, not text.\n\n"
                "📸 **Please upload your photo**\n\n"
                "💡 *How to upload a photo:*\n"
                "1. Tap the 📎 (attachment) button\n"
                "2. Select 'Photo' or 'Camera'\n"
                "3. Take a photo or choose from gallery\n"
                "4. Send it to me\n\n"
                "⚠️ *Make sure it's a clear photo of your face*",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO
        
        # If user sent a document (e.g., PNG with transparency), accept it and preserve alpha
        if update.message.document:
            try:
                doc = update.message.document
                file = await context.bot.get_file(doc.file_id)
                file_bytes = await file.download_as_bytearray()
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(file_bytes))
                # Convert to RGBA to preserve transparency if present
                img = img.convert('RGBA')
                filename = 'photo_temp.png'
                filepath = self._user_static_path(user_id, filename)
                img.save(filepath, format='PNG')
                self.user_sessions[user_id]['files']['custom_photo'] = file_bytes
                await update.message.reply_text(
                    "✅ **Photo Uploaded (Document) Successfully!**\n\n"
                    "📸 Transparency preserved if present.\n\n"
                    "⚙️ **Next Step:** Configure your ID generation options",
                    parse_mode=ParseMode.MARKDOWN
                )
                return await self.show_generation_options(update, context, user_id)
            except Exception as e:
                await update.message.reply_text(
                    "❌ *Photo Document Processing Error*\n\n"
                    f"🔧 **Error:** {str(e)}\n\n"
                    "💡 Try sending the image as a PNG document again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PHOTO
        
        # Check if user sent other file types
        if update.message.video or update.message.audio or update.message.voice:
            await update.message.reply_text(
                "❌ *Wrong File Type*\n\n"
                "I need a **photo**, not a video or audio file.\n\n"
                "📸 **Please upload your photo**\n\n"
                "✅ **Accepted:** Photos (JPEG, PNG)\n"
                "❌ **Not accepted:** Videos, audio, documents, etc.\n\n"
                "💡 *How to upload:*\n"
                "1. Tap 📎 (attachment)\n"
                "2. Select 'Photo' or 'Camera'\n"
                "3. Take/choose your photo\n"
                "4. Send it",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO
        
        # Check if photo exists
        if not update.message.photo:
            await update.message.reply_text(
                "❌ *No Photo Received*\n\n"
                "I didn't receive any photo from you.\n\n"
                "📸 **Please upload your photo**\n\n"
                "💡 *How to upload:*\n"
                "1. Tap 📎 (attachment)\n"
                "2. Select 'Photo' or 'Camera'\n"
                "3. Take/choose your photo\n"
                "4. Send it",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO
        
        try:
            # Get the largest photo size
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            photo_bytes = await file.download_as_bytearray()
            
            # Check file size (limit to 5MB)
            file_size = photo.file_size
            if file_size and file_size > 5 * 1024 * 1024:  # 5MB
                await update.message.reply_text(
                    "❌ *Photo Too Large*\n\n"
                    f"📏 **Size:** {file_size / (1024*1024):.1f} MB\n"
                    "❌ **Limit:** 5 MB maximum\n\n"
                    "💡 *Solutions:*\n"
                    "• Take a new photo with lower resolution\n"
                    "• Compress the photo before uploading\n"
                    "• Use a different photo\n\n"
                    "🔄 **Try again:** Upload a smaller photo",
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PHOTO
            
            # Save custom photo. Telegram photos are typically JPEG (no alpha).
            # We still normalize to PNG; for transparency, ask user to send as Document (keeps alpha).
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(photo_bytes)).convert('RGBA')
            filename = 'photo_temp.png'
            filepath = self._user_static_path(user_id, filename)
            img.save(filepath, format='PNG')
            
            self.user_sessions[user_id]['files']['custom_photo'] = photo_bytes
            
            # Success message
            await update.message.reply_text(
                "✅ **Photo Uploaded Successfully!**\n\n"
                f"📏 **Size:** {file_size / 1024:.1f} KB\n"
                "📸 **Type:** Custom photo\n\n"
                "⚙️ **Next Step:** Configure your ID generation options\n\n"
                "💡 *Note:* To preserve transparency, send the image as a PNG document (File), not as a compressed photo.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return await self.show_generation_options(update, context, user_id)
            
        except Exception as e:
            await update.message.reply_text(
                "❌ *Photo Processing Error*\n\n"
                "I couldn't process your photo.\n\n"
                "🔍 **Possible issues:**\n"
                "• File is corrupted\n"
                "• Unsupported image format\n"
                "• File is too large\n"
                "• Network error during upload\n\n"
                "💡 *Try again:*\n"
                "• Upload a different photo\n"
                "• Make sure it's a clear image\n"
                "• Try a smaller file size\n\n"
                f"🔧 **Technical error:** {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PHOTO

    async def show_generation_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        # Backward-compatible entry that now starts with BG options
        return await self.show_background_options(update, context, user_id)

    async def show_background_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        # Show background removal options - simplified to None and BG Remover
        keyboard = [
            [InlineKeyboardButton("❌ None", callback_data="bg_none")],
            [InlineKeyboardButton("🖼️ BG Remover", callback_data="bg_remover")]
        ]
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                self.get_text_for_user({'language': 'am'}, 'choose_background'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=self.get_text_for_user({'language': 'am'}, 'choose_background'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return CONFIRMING_DATA

    # New: output variant selection and handling
    async def show_output_variant_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        data = self.user_sessions[user_id]['data']
        id_type = data.get('id_type', 'normal')
        if id_type == 'mini':
            keyboard = [
                [InlineKeyboardButton("Front Color", callback_data="variant_mini_front_color")],
                [InlineKeyboardButton("Front Grayscale", callback_data="variant_mini_front_bw")],
            ]
        elif id_type == 'old':
            keyboard = [
                [InlineKeyboardButton("Front Color", callback_data="variant_old_front_color")],
                [InlineKeyboardButton("Front Grayscale", callback_data="variant_old_front_bw")],
                [InlineKeyboardButton("Reverse Color", callback_data="variant_old_reverse_color")],
                [InlineKeyboardButton("Reverse Grayscale", callback_data="variant_old_reverse_bw")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("Front Color", callback_data="variant_front_color")],
                [InlineKeyboardButton("Front Grayscale", callback_data="variant_front_bw")],
                [InlineKeyboardButton("Reverse Color", callback_data="variant_reverse")],
                [InlineKeyboardButton("Reverse Grayscale", callback_data="variant_reverse_bw")],
            ]
        prompt = "Choose which single ID image to generate:"
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(prompt, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.send_message(chat_id=user_id, text=prompt, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRMING_DATA

    # Consolidated Settings menu
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        # Ensure user session exists
        if user_id not in self.user_sessions:
            # Initialize with default preferences
            default_prefs = {
                    'id_type': None,
                    'output_variant': None,
                    'city_type': None,
                    'mode': 'detail',
                    'language': 'en',
            }
            
            # Initialize data with preserved settings from prefs
            initial_data = {}
            if 'id_type' in default_prefs:
                initial_data['id_type'] = default_prefs['id_type']
            if 'remove_white_bg' in default_prefs:
                initial_data['remove_white_bg'] = default_prefs['remove_white_bg']
            if 'remove_black_bg' in default_prefs:
                initial_data['remove_black_bg'] = default_prefs['remove_black_bg']
            if 'output_variant' in default_prefs:
                initial_data['output_variant'] = default_prefs['output_variant']
            if 'city_type' in default_prefs:
                initial_data['city_type'] = default_prefs['city_type']
            if 'generate_old_id' in default_prefs:
                initial_data['generate_old_id'] = default_prefs['generate_old_id']
            if 'generate_mini_id' in default_prefs:
                initial_data['generate_mini_id'] = default_prefs['generate_mini_id']
                
            self.user_sessions[user_id] = {
                'data': initial_data,
                'files': {},
                'edit_field': None,
                'edit_mode': None,
                'current_edit_index': 0,
                'prefs': default_prefs,
                'preview_visible': False,
                'preview_message_id': None
            }
        else:
            # Ensure prefs exists and has default values for missing keys
            if 'prefs' not in self.user_sessions[user_id]:
                self.user_sessions[user_id]['prefs'] = {}
            prefs = self.user_sessions[user_id]['prefs']
            if 'mode' not in prefs:
                prefs['mode'] = 'default'
            if 'language' not in prefs:
                    prefs['language'] = 'am'
        
        data = self.user_sessions[user_id]['data']
        prefs = self.user_sessions[user_id]['prefs']
        
        bg = 'BG Remover' if (data.get('remove_white_bg') or data.get('remove_black_bg')) else 'None'

        # Fix output variant display - simplified to Color or Grayscale
        variant_raw = data.get('output_variant') or 'reverse'
        if 'bw' in variant_raw or 'grayscale' in variant_raw:
            variant = 'Grayscale'
        else:
            variant = 'Color'
        
        # Fix ID type display
        id_type_raw = data.get('id_type') or 'normal'
        if id_type_raw == 'old':
            id_type = 'Old ID'
        elif id_type_raw == 'mini':
            id_type = 'Mini ID'
        else:
            id_type = 'Normal ID'
            
        mode = (prefs.get('mode') or 'default').title()
        language = (prefs.get('language') or 'am').upper()

        text = get_text(prefs, 'settings', 
                       bg=bg, id_type=id_type, variant=variant, 
                       city='', mode=mode, language=language)
        
        keyboard = [
            [InlineKeyboardButton("Background Remover", callback_data="settings_bg")],
            [InlineKeyboardButton("ID Type", callback_data="settings_idtype"), InlineKeyboardButton("Output Variant", callback_data="settings_variant")],
            [InlineKeyboardButton("Mode", callback_data="settings_mode"), InlineKeyboardButton("Language", callback_data="settings_lang")],
            [InlineKeyboardButton(get_text(prefs, 'close'), callback_data="back_to_start")]
        ]
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_settings_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data

        if choice == 'settings_bg':
            # Show background options with buttons - simplified to None and BG Remover
            keyboard = [
                [InlineKeyboardButton("❌ None", callback_data="bg_none")],
                [InlineKeyboardButton("🖼️ BG Remover", callback_data="bg_remover")],
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_back")]
            ]
            prefs = self.user_sessions[user_id]['prefs']
            await query.edit_message_text(get_text(prefs, 'bg_options'), reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA
            
        if choice == 'settings_idtype':
            # Show ID type options with buttons
            keyboard = [
                [InlineKeyboardButton("📄 Normal ID", callback_data="id_normal")],
                [InlineKeyboardButton("🆔 Mini ID", callback_data="id_mini")],
                [InlineKeyboardButton("📜 Old ID", callback_data="id_old")],
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_back")]
            ]
            prefs = self.user_sessions[user_id]['prefs']
            await query.edit_message_text(get_text(prefs, 'id_type_options'), reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA
            
        if choice == 'settings_variant':
            # Show output variant options with buttons - simplified to Color and Grayscale
            keyboard = [
                [InlineKeyboardButton("🎨 Color", callback_data="variant_color")],
                [InlineKeyboardButton("⚫ Grayscale", callback_data="variant_grayscale")],
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_back")]
            ]
            prefs = self.user_sessions[user_id]['prefs']
            await query.edit_message_text(get_text(prefs, 'variant_options'), reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA
        if choice == 'settings_mode':
            prefs = self.user_sessions[user_id]['prefs']
            keyboard = [
                [InlineKeyboardButton(get_text(prefs, 'mode_detail'), callback_data="mode_detail")],
                [InlineKeyboardButton(get_text(prefs, 'mode_default'), callback_data="mode_default")],
                [InlineKeyboardButton(get_text(prefs, 'back'), callback_data="settings_back")]
            ]
            await query.edit_message_text(get_text(prefs, 'mode_options'), reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA
        if choice == 'settings_lang':
            prefs = self.user_sessions[user_id]['prefs']
            keyboard = [
                [InlineKeyboardButton(get_text(prefs, 'lang_english'), callback_data="lang_en")],
                [InlineKeyboardButton(get_text(prefs, 'lang_amharic'), callback_data="lang_am")],
                [InlineKeyboardButton(get_text(prefs, 'back'), callback_data="settings_back")]
            ]
            await query.edit_message_text(get_text(prefs, 'lang_options'), reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA
        if choice == 'settings_start_pdf':
            prefs = self.user_sessions[user_id]['prefs']
            await query.edit_message_text(
                get_text(prefs, 'ready_start'),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PDF
        if choice == 'settings_back':
            # Return to main settings menu
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA
        if choice == 'data_unhide':
            # Return to main settings menu from settings
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA
        if choice == 'back_to_start':
            # Return to main welcome message (render via callback-safe edit)
            user_name = update.effective_user.first_name or "Unknown"
            prefs = self.user_sessions[user_id]['prefs']
            welcome = get_text(prefs, 'welcome', name=user_name)
            keyboard = [[InlineKeyboardButton("⚙️ Settings", callback_data="quick_settings")]]
            await query.edit_message_text(
                welcome,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END

        return CONFIRMING_DATA

    async def handle_unauthorized_language_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language selection for unauthorized users before showing access denied message"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data
        
        # Determine selected language
        selected_language = 'am'  # Default to Amharic
        if choice == 'unauthorized_lang_en':
            selected_language = 'en'
        elif choice == 'unauthorized_lang_am':
            selected_language = 'am'
        
        # Save the user's language preference permanently
        self.set_user_language(user_id, selected_language)
        
        # Show access denied message in selected language
        await query.edit_message_text(
            self.get_unauthorized_message(user_id),
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    async def handle_mode_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data
        
        if choice == 'mode_detail':
            self.user_sessions[user_id]['prefs']['mode'] = 'detail'
        elif choice == 'mode_default':
            self.user_sessions[user_id]['prefs']['mode'] = 'default'
        elif choice == 'settings_back':
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA
        
        # Sync to Firebase
        self._sync_preferences_to_firebase(user_id)
        
        await self.show_settings_menu(update, context, user_id)
        return CONFIRMING_DATA

    async def handle_language_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data
        
        if choice == 'lang_en':
            self.user_sessions[user_id]['prefs']['language'] = 'en'
            self.set_user_language(user_id, 'en')  # Save permanently
        elif choice == 'lang_am':
            self.user_sessions[user_id]['prefs']['language'] = 'am'
            self.set_user_language(user_id, 'am')  # Save permanently
        elif choice == 'settings_back':
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA
        
        # Check if this is initial language selection for a new user
        if user_id not in self.user_sessions:
            # Initialize user session for new user who just selected language
            user_lang = self.get_user_language(user_id)
            self.user_sessions[user_id] = {
                'data': {}, 
                'files': {}, 
                'edit_field': None,
                'edit_mode': None,
                'current_edit_index': 0,
                'prefs': {
                    'id_type': None,
                    'output_variant': None,
                    'city_type': None,
                    'mode': 'default',
                    'language': user_lang,
                },
                'preview_visible': False,
                'preview_message_id': None
            }
            
            # Show welcome message for new user
            user_name = query.from_user.first_name or "Unknown"
            
            # Get user's ID generation stats
            stats = self.daily_service.get_user_stats(user_id)
            today_count = stats["today_count"]
            
            # Add ID count to welcome message
            welcome = get_text(self.user_sessions[user_id]['prefs'], 'welcome', name=user_name)
            if today_count > 0:
                welcome += f"\n\n📊 **Your Stats Today:**\n✅ IDs Generated: {today_count}\n📈 Total Unpaid Generated: {stats.get('total_unpaid', 0)}"
            
            # Add only one settings button
            keyboard = [
                [InlineKeyboardButton("⚙️ Settings", callback_data="quick_settings")]
            ]
            
            await query.edit_message_text(
                welcome, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_PDF
        else:
            # This is from settings menu
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA

    async def handle_output_variant(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        variant_choice = query.data.replace('variant_', '')
        
        # Map simplified color/grayscale to internal variant based on ID type
        id_type = self.user_sessions[user_id]['data'].get('id_type', 'normal')
        
        if variant_choice == 'color':
            if id_type == 'mini':
                variant = 'mini_front_color'
            elif id_type == 'old':
                variant = 'old_front_color'
            else:
                variant = 'reverse'  # Normal ID default to reverse color
        elif variant_choice == 'grayscale':
            if id_type == 'mini':
                variant = 'mini_front_bw'
            elif id_type == 'old':
                variant = 'old_front_bw'
            else:
                variant = 'reverse_bw'  # Normal ID default to reverse grayscale
        else:
            variant = variant_choice  # Fallback for other variants
        
        self.user_sessions[user_id]['data']['output_variant'] = variant
        # Save defaults for next time
        prefs = self.user_sessions[user_id].get('prefs', {})
        prefs['output_variant'] = variant
        prefs['id_type'] = id_type
        self.user_sessions[user_id]['prefs'] = prefs
        
        # Sync to Firebase
        self._sync_preferences_to_firebase(user_id)
        
        # After selecting variant, return to Settings
        await self.show_settings_menu(update, context, user_id)
        return CONFIRMING_DATA

    async def show_id_type_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        # Show ID type options separately
        keyboard = [
            [InlineKeyboardButton("Normal ID Cards", callback_data="id_normal")],
            [InlineKeyboardButton("Generate Mini ID Cards", callback_data="mini_id")],
            [InlineKeyboardButton("Generate Old ID Cards", callback_data="old_id")]
        ]
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                self.get_text_for_user({'language': 'am'}, 'choose_id_type'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=self.get_text_for_user({'language': 'am'}, 'choose_id_type'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return CONFIRMING_DATA

    async def handle_bg_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        bg_option = query.data
        # Handle background removal options - simplified to None and BG Remover
        # BG Remover removes white background by default
        if bg_option == 'bg_remover':
            self.user_sessions[user_id]['data']['remove_white_bg'] = True
            self.user_sessions[user_id]['data']['remove_black_bg'] = False
        else:  # bg_none
            self.user_sessions[user_id]['data']['remove_white_bg'] = False
            self.user_sessions[user_id]['data']['remove_black_bg'] = False
        
        # Also save to prefs for persistence
        if 'prefs' not in self.user_sessions[user_id]:
            self.user_sessions[user_id]['prefs'] = {}
        self.user_sessions[user_id]['prefs']['remove_white_bg'] = self.user_sessions[user_id]['data']['remove_white_bg']
        self.user_sessions[user_id]['prefs']['remove_black_bg'] = self.user_sessions[user_id]['data']['remove_black_bg']
        # Reset id type flags for clarity; will be set next
        self.user_sessions[user_id]['data']['generate_old_id'] = False
        self.user_sessions[user_id]['data']['generate_mini_id'] = False

        # Sync preferences to Firebase
        self._sync_preferences_to_firebase(user_id)

        # After choosing BG option, return to Settings
        await self.show_settings_menu(update, context, user_id)
        return CONFIRMING_DATA

    async def handle_id_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END

        id_choice = query.data
        if id_choice == 'mini_id':
            self.user_sessions[user_id]['data']['generate_mini_id'] = True
            self.user_sessions[user_id]['data']['generate_old_id'] = False
            self.user_sessions[user_id]['data']['id_type'] = 'mini'
            # Sensible default variant for mini
            self.user_sessions[user_id]['data']['output_variant'] = 'mini_front_color'
        elif id_choice == 'old_id':
            self.user_sessions[user_id]['data']['generate_old_id'] = True
            self.user_sessions[user_id]['data']['generate_mini_id'] = False
            self.user_sessions[user_id]['data']['id_type'] = 'old'
            # Sensible default variant for old
            self.user_sessions[user_id]['data']['output_variant'] = 'old_front_color'
        else:  # id_normal
            self.user_sessions[user_id]['data']['generate_old_id'] = False
            self.user_sessions[user_id]['data']['generate_mini_id'] = False
            self.user_sessions[user_id]['data']['id_type'] = 'normal'
            # Default to reverse color for normal
            self.user_sessions[user_id]['data']['output_variant'] = 'reverse'

        # Persist preference
        prefs = self.user_sessions[user_id].get('prefs', {})
        prefs['id_type'] = self.user_sessions[user_id]['data']['id_type']
        prefs['output_variant'] = self.user_sessions[user_id]['data']['output_variant']
        prefs['generate_old_id'] = self.user_sessions[user_id]['data']['generate_old_id']
        prefs['generate_mini_id'] = self.user_sessions[user_id]['data']['generate_mini_id']
        self.user_sessions[user_id]['prefs'] = prefs

        # Sync preferences to Firebase
        self._sync_preferences_to_firebase(user_id)

        # Debug: Print current settings
        print(f"DEBUG: ID type changed to: {self.user_sessions[user_id]['data']['id_type']}")
        print(f"DEBUG: Output variant: {self.user_sessions[user_id]['data']['output_variant']}")
        print(f"DEBUG: Generate old ID: {self.user_sessions[user_id]['data']['generate_old_id']}")
        print(f"DEBUG: Generate mini ID: {self.user_sessions[user_id]['data']['generate_mini_id']}")

        # After choosing ID type, return to Settings
        await self.show_settings_menu(update, context, user_id)
        return CONFIRMING_DATA

    async def handle_city_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        city_type = query.data
        self.user_sessions[user_id]['data']['city_type'] = city_type
        # Save default city type
        prefs = self.user_sessions[user_id].get('prefs', {})
        prefs['city_type'] = city_type
        self.user_sessions[user_id]['prefs'] = prefs
        
        # Sync to Firebase
        self._sync_preferences_to_firebase(user_id)
        
        # After city type, return to Settings
        await self.show_settings_menu(update, context, user_id)
        return CONFIRMING_DATA

    async def show_data_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        data = self.user_sessions[user_id]['data']
        
        # Create a comprehensive data review message
        text = "*📋 Review Your Information:*\n\n"
        
        # Personal Information
        text += "*👤 Personal Information:*\n"
        text += f"• Name (EN): `{data.get('name_en', 'N/A')}`\n"
        text += f"• Name (AM): `{data.get('name_am', 'N/A')}`\n"
        text += f"• Gender (EN): `{data.get('gender_en', 'N/A')}`\n"
        text += f"• Gender (AM): `{data.get('gender_am', 'N/A')}`\n"
        text += f"• DOB (EN): `{data.get('dob_en', 'N/A')}`\n"
        text += f"• DOB (AM): `{data.get('dob_am', 'N/A')}`\n"
        text += f"• Phone: `{data.get('phone', 'N/A')}`\n\n"
        
        # Address Information
        text += "*🏠 Address Information:*\n"
        text += f"• Region (EN): `{data.get('region_en', 'N/A')}`\n"
        text += f"• Region (AM): `{data.get('region_am', 'N/A')}`\n"
        text += f"• Subcity (EN): `{data.get('subcity_en', 'N/A')}`\n"
        text += f"• Subcity (AM): `{data.get('subcity_am', 'N/A')}`\n"
        text += f"• Woreda (EN): `{data.get('woreda_en', 'N/A')}`\n"
        text += f"• Woreda (AM): `{data.get('woreda_am', 'N/A')}`\n\n"
        
        # Nationality
        text += "*🌍 Nationality:*\n"
        text += f"• Nationality (EN): `{data.get('nationality_en', 'N/A')}`\n"
        text += f"• Nationality (AM): `{data.get('nationality_am', 'N/A')}`\n\n"
        
        # Generation Options
        text += "*⚙️ Generation Options:*\n"
        text += f"• ID Type: `{data.get('id_type', 'normal')}`\n"
        text += f"• Output Variant: `{data.get('output_variant', 'front_color')}`\n"
        text += f"• City Type: `{data.get('city_type', 'default')}`\n"
        text += f"• Remove White BG: `{data.get('remove_white_bg', False)}`\n"
        text += f"• Remove Black BG: `{data.get('remove_black_bg', False)}`\n"
        
        # Create keyboard with editing options
        keyboard = [
            [InlineKeyboardButton("👁️ Hide Preview", callback_data="data_hide"), InlineKeyboardButton("✏️ Edit", callback_data="edit_personal")],
            [InlineKeyboardButton("🔁 Replace Photo", callback_data="photo_replace"), InlineKeyboardButton("❌ Cancel", callback_data="data_cancel")],
            [InlineKeyboardButton("🚀 Generate ID", callback_data="generate")]
        ]
        
        # Determine if this is a callback query or message
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def show_compact_controls(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, replace: bool = False) -> None:
        """Show a compact control panel with preview hidden by default."""
        keyboard = [
            [InlineKeyboardButton("👁️ Unhide Preview", callback_data="data_unhide"), InlineKeyboardButton("✏️ Edit", callback_data="edit_personal")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="edit_options"), InlineKeyboardButton("❌ Cancel", callback_data="data_cancel")],
            [InlineKeyboardButton("🚀 Generate ID", callback_data="generate")]
        ]
        prefs = self.user_sessions[user_id].get('prefs', {'language': 'en'})
        text = get_text(prefs, 'settings_prompt')
        if hasattr(update, 'callback_query') and update.callback_query:
            if replace:
                await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_edit_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        choice = query.data
        
        if choice == "generate":
            # Proceed to ID generation
            await query.edit_message_text("🚀 Generating your digital ID cards...")
            await self.generate_id(update, context, user_id)
            return ConversationHandler.END
        elif choice == "edit_personal":
            return await self.show_personal_edit_options(update, context, user_id)
        elif choice == "edit_address":
            return await self.show_address_edit_options(update, context, user_id)
        elif choice == "edit_nationality":
            return await self.show_nationality_edit_options(update, context, user_id)
        elif choice == "edit_options":
            await self.show_settings_menu(update, context, user_id)
            return CONFIRMING_DATA
        
        return CONFIRMING_DATA

    async def show_personal_edit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        personal_fields = [f for f in EDITABLE_FIELDS if f not in ADDRESS_FIELDS + NATIONALITY_FIELDS]
        keyboard = []
        for field in personal_fields:
            keyboard.append([InlineKeyboardButton(f"Edit {field}", callback_data=f"edit_{field}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Review", callback_data="back_to_review")])
        
        await update.callback_query.edit_message_text(
            "Select a personal information field to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMING_DATA

    async def show_address_edit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        keyboard = []
        for field in ADDRESS_FIELDS:
            keyboard.append([InlineKeyboardButton(f"Edit {field}", callback_data=f"edit_{field}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Review", callback_data="back_to_review")])
        
        await update.callback_query.edit_message_text(
            "Select an address field to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMING_DATA

    async def show_nationality_edit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
        keyboard = []
        for field in NATIONALITY_FIELDS:
            keyboard.append([InlineKeyboardButton(f"Edit {field}", callback_data=f"edit_{field}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Review", callback_data="back_to_review")])
        
        await update.callback_query.edit_message_text(
            "Select a nationality field to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMING_DATA

    async def handle_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = (
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the administrator to get access.\n\n"
                f"Your User ID: `{user_id}`"
            )
            await query.edit_message_text(self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        choice = query.data
        
        if choice == "back_to_review":
            await self.show_data_review(update, context, user_id)
            return CONFIRMING_DATA
        
        if choice.startswith("edit_"):
            field = choice.replace("edit_", "")
            self.user_sessions[user_id]['edit_field'] = field
            current_value = self.user_sessions[user_id]['data'].get(field, 'N/A')
            await query.edit_message_text(
                f"Current value for `{field}`: `{current_value}`\n\n"
                f"Send the new value for `{field}`:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIELD_VALUE
        
        return CONFIRMING_DATA

    async def handle_field_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        field = self.user_sessions[user_id]['edit_field']
        value = update.message.text.strip()
        
        # Check if value is empty
        if not value:
            await update.message.reply_text(
                "❌ *Empty Value*\n\n"
                f"The field `{field}` cannot be empty.\n\n"
                "💡 *Please provide a valid value*\n\n"
                f"📝 **Current field:** `{field}`\n"
                "🔄 **Try again:** Send a valid value",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIELD_VALUE
        
        # Validate specific field types
        validation_error = self._validate_field_value(field, value)
        if validation_error:
            await update.message.reply_text(
                f"❌ *Invalid Value*\n\n"
                f"**Field:** `{field}`\n"
                f"**Value:** `{value}`\n\n"
                f"**Problem:** {validation_error}\n\n"
                "🔄 **Try again:** Send a valid value",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIELD_VALUE
        
        # Update the field value
        self.user_sessions[user_id]['data'][field] = value
        
        # Update combined address fields if address components were changed
        if field in ['region_am', 'region_en', 'subcity_am', 'subcity_en', 'woreda_am', 'woreda_en']:
            data = self.user_sessions[user_id]['data']
            if all(key in data for key in ['region_am', 'subcity_am', 'woreda_am']):
                data["address_am"] = f"{data['region_am']}, {data['subcity_am']}, {data['woreda_am']}"
            if all(key in data for key in ['region_en', 'subcity_en', 'woreda_en']):
                data["address_en"] = f"{data['region_en']}, {data['subcity_en']}, {data['woreda_en']}"
        
        # Success message
        await update.message.reply_text(
            f"✅ **Field Updated Successfully!**\n\n"
            f"📝 **Field:** `{field}`\n"
            f"📋 **New Value:** `{value}`\n\n"
            "📋 **Next:** Review your updated information",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await self.show_data_review(update, context, user_id)
        return CONFIRMING_DATA

    def _validate_field_value(self, field: str, value: str) -> str:
        """Validate field values and return error message if invalid"""
        
        # Phone number validation
        if field == 'phone':
            # Remove spaces, dashes, and parentheses
            clean_phone = ''.join(c for c in value if c.isdigit())
            if not clean_phone.isdigit():
                return "Phone number should contain only numbers"
            if len(clean_phone) < 9 or len(clean_phone) > 15:
                return f"Phone number should be 9-15 digits (got {len(clean_phone)})"
            return None
        
        # Date validation for DOB fields
        if field in ['dob_en', 'dob_am']:
            # Basic date format validation
            if '/' not in value and '-' not in value:
                return "Date should be in format DD/MM/YYYY or YYYY-MM-DD"
            return None
        
        # Name validation
        if field in ['name_en', 'name_am']:
            if len(value) < 2:
                return "Name should be at least 2 characters long"
            if len(value) > 100:
                return "Name should be less than 100 characters"
            return None
        
        # Address validation
        if field in ['region_en', 'region_am', 'subcity_en', 'subcity_am', 'woreda_en', 'woreda_am']:
            if len(value) < 2:
                return "Address field should be at least 2 characters long"
            if len(value) > 50:
                return "Address field should be less than 50 characters"
            return None
        
        # Nationality validation
        if field in ['nationality_en', 'nationality_am']:
            if len(value) < 2:
                return "Nationality should be at least 2 characters long"
            if len(value) > 30:
                return "Nationality should be less than 30 characters"
            return None
        
        # Gender validation
        if field in ['gender_en', 'gender_am']:
            valid_genders = ['male', 'female', 'ወንድ', 'ሴት', 'Male', 'Female']
            if value.lower() not in [g.lower() for g in valid_genders]:
                return "Gender should be 'Male'/'Female' or 'ወንድ'/'ሴት'"
            return None
        
        # Default validation
        if len(value) > 200:
            return "Value should be less than 200 characters"
        
        return None

    async def generate_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        data = self.user_sessions[user_id]['data']
        remove_white = data.get('remove_white_bg', False)
        remove_black = data.get('remove_black_bg', False)
        city_type = data.get('city_type', 'default')
        generate_old_id = data.get('generate_old_id', False)
        generate_mini_id = data.get('generate_mini_id', False)
        
        # Get user name for tracking
        user_name = update.effective_user.first_name or "Unknown User"
        
        # Add address fields if not present
        if all(key in data for key in ['region_am', 'subcity_am', 'woreda_am']):
            data["address_am"] = f"{data['region_am']}, {data['subcity_am']}, {data['woreda_am']}"
        if all(key in data for key in ['region_en', 'subcity_en', 'woreda_en']):
            data["address_en"] = f"{data['region_en']}, {data['subcity_en']}, {data['woreda_en']}"
        
        try:
            # Send initial processing message
            processing_msg = await context.bot.send_message(
                chat_id=user_id,
                text=self.get_text_for_user({'language': 'am'}, 'processing_id'),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Generate ID cards with timeout handling
            import asyncio
            try:
                # Run the generation in a thread to avoid blocking with a 120-second timeout
                loop = asyncio.get_event_loop()
                generated_files = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, 
                        lambda: self.id_service.generate_id_card(
                            data, 
                            city_option=city_type, 
                            remove_white=remove_white, 
                            remove_black=remove_black,
                            generate_old_id=generate_old_id,
                            generate_mini_id=generate_mini_id
                        )
                    ),
                    timeout=120.0  # 2 minutes timeout for image generation
                )
            except asyncio.TimeoutError:
                await processing_msg.edit_text(
                    "⏰ Generation timeout. Please try again or start a new session."
                )
                return
            except Exception as gen_error:
                await processing_msg.edit_text(
                    f"❌ Generation error: {str(gen_error)}\nPlease try again or start a new session."
                )
                return
            
            # Determine single output variant to send
            variant = self.user_sessions[user_id]['data'].get('output_variant')
            # Default variant depending on id type
            if not variant:
                if generate_mini_id:
                    variant = 'mini_front_color'
                elif generate_old_id:
                    variant = 'old_front_color'
                else:
                    variant = 'reverse'
            # Map variants if ID type changed without updating variant
            if generate_old_id and not variant.startswith('old_'):
                mapping = {
                    'front_color': 'old_front_color',
                    'front_bw': 'old_front_bw',
                    'reverse': 'old_reverse_color',
                    'reverse_bw': 'old_reverse_bw'
                }
                variant = mapping.get(variant, 'old_front_color')
            if generate_mini_id and not variant.startswith('mini_'):
                mapping = {
                    'front_color': 'mini_front_color',
                    'front_bw': 'mini_front_bw',
                }
                variant = mapping.get(variant, 'mini_front_color')

            # Update processing message
            filename = generated_files.get(variant)
            if not filename:
                await processing_msg.edit_text(
                    "❌ Generation error. Could not create the selected ID variant." + self.get_support_footer()
                )
                return
            path = os.path.join(self.id_service.config.STATIC_FOLDER, filename)
            if not os.path.exists(path):
                await processing_msg.edit_text(
                    "❌ File missing. The output file was not found." + self.get_support_footer()
                )
                return

            await processing_msg.edit_text("✅ ID generated! Sending your image...")
            try:
                with open(path, 'rb') as img_file:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=InputFile(img_file, filename=filename)
                    )
            except Exception as send_error:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(self.get_text_for_user({'language': 'am'}, 'send_error') + f" {send_error}" + self.get_support_footer())
                )
                return

            # Track successful ID generation
            try:
                stats = self.daily_service.increment_id_count(user_id, user_name)
                success_message = self.get_text_for_user({'language': 'am'}, 'access_granted', 
                                                        today_count=stats['today_count'], 
                                                        total_unpaid=stats['total_unpaid'])
            except Exception as e:
                print(f"Error tracking ID generation: {str(e)}")
                success_message = self.get_text_for_user({'language': 'am'}, 'id_ready')

            await context.bot.send_message(
                chat_id=user_id,
                text=success_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            error_msg = str(e)
            if "Timed out" in error_msg:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(self.get_text_for_user({'language': 'am'}, 'timeout_error') + self.get_support_footer())
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(f"{self.get_text_for_user({'language': 'am'}, 'generation_error')} {error_msg}\nእባክዎ እንደገና ይሞክሩ ወይም አዲስ ክፍለ-ጊዜ ይጀምሩ።" + self.get_support_footer())
                )
        
        # Clear session but preserve user preferences and settings for next use
        current_session = self.user_sessions.get(user_id, {})
        preserved_prefs = current_session.get('prefs', {
            'mode': 'default',
            'language': 'am'
        })
        
        # Preserve important settings from data section
        current_data = current_session.get('data', {})
        if 'id_type' in current_data:
            preserved_prefs['id_type'] = current_data['id_type']
        if 'remove_white_bg' in current_data:
            preserved_prefs['remove_white_bg'] = current_data['remove_white_bg']
        if 'remove_black_bg' in current_data:
            preserved_prefs['remove_black_bg'] = current_data['remove_black_bg']
        if 'output_variant' in current_data:
            preserved_prefs['output_variant'] = current_data['output_variant']
        if 'city_type' in current_data:
            preserved_prefs['city_type'] = current_data['city_type']
        if 'generate_old_id' in current_data:
            preserved_prefs['generate_old_id'] = current_data['generate_old_id']
        if 'generate_mini_id' in current_data:
            preserved_prefs['generate_mini_id'] = current_data['generate_mini_id']
            
        self.user_sessions.pop(user_id, None)
        # Re-initialize with preserved preferences
        self.user_sessions[user_id] = {
            'prefs': preserved_prefs
        }

    async def compress_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Compress a PDF file to reduce its size with multiple compression options"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not self.is_user_authorized(user_id):
            unauthorized_message = self.get_text_for_user({'language': 'am'}, 'access_denied_short', user_id=user_id)
            await update.message.reply_text(unauthorized_message, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        # Check if user has a PDF in their session
        if not self.user_sessions.get(user_id, {}).get('files', {}).get('pdf'):
            await update.message.reply_text(
                "❌ *No PDF to Compress*\n\n"
                "You need to upload a PDF first before compressing it.\n\n"
                "📄 **Steps:**\n"
                "1. Upload your PDF file\n"
                "2. Send your FIN number\n"
                "3. Then use /compress to reduce its size\n\n"
                "💡 *Or send a PDF link to compress it directly*",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Get the PDF from session
        pdf_bytes = self.user_sessions[user_id]['files']['pdf']
        original_size = len(pdf_bytes)
        
        # Show compression options
        keyboard = [
            [InlineKeyboardButton("🚀 Fast Compression (Quick)", callback_data="compress_fast")],
            [InlineKeyboardButton("⚡ Standard Compression (Balanced)", callback_data="compress_standard")],
            [InlineKeyboardButton("🔥 Maximum Compression (Slow)", callback_data="compress_maximum")],
            [InlineKeyboardButton("🖼️ Image Compression (Photo-heavy PDFs)", callback_data="compress_images")],
            [InlineKeyboardButton("📄 Page Limit (First 10 pages)", callback_data="compress_pages")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🗜️ **Choose Compression Method**\n\n"
            f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
            f"📏 **Size:** {original_size / (1024*1024):.1f} MB\n\n"
            "🎯 **Select your preferred method:**\n\n"
            "🚀 **Fast:** Quick compression, moderate size reduction\n"
            "⚡ **Standard:** Balanced speed and compression\n"
            "🔥 **Maximum:** Best compression, takes longer\n"
            "🖼️ **Image:** Optimized for photo-heavy PDFs\n"
            "📄 **Pages:** Keep only first 10 pages",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END

    async def _compress_pdf_bytes(self, pdf_bytes: bytes) -> bytes:
        """Compress PDF bytes to reduce file size with multiple fallback methods"""
        original_size = len(pdf_bytes)
        
        # Method 1: Try PyPDF2 with aggressive compression
        try:
            import PyPDF2
            from io import BytesIO
            
            # Read the PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy all pages with compression
            for page in pdf_reader.pages:
                # Compress the page content streams
                page.compress_content_streams()
                pdf_writer.add_page(page)
            
            # Write compressed PDF to bytes
            output = BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            compressed = output.getvalue()
            if len(compressed) < original_size:
                print(f"PyPDF2 compression: {original_size} -> {len(compressed)} bytes")
                return compressed
                
        except Exception as e:
            print(f"PyPDF2 compression failed: {e}")
        
        # Method 2: Try PyMuPDF with aggressive compression
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Create new document with maximum compression
            new_doc = fitz.open()
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            # Save with maximum compression settings
            output = BytesIO()
            new_doc.save(output, 
                        garbage=4,           # Maximum garbage collection
                        deflate=True,        # Use deflate compression
                        clean=True,          # Clean unused objects
                        linear=True,         # Linearize for web
                        pretty=False,        # Minimize whitespace
                        ascii=False)         # Use binary for smaller size
            
            output.seek(0)
            compressed = output.getvalue()
            
            doc.close()
            new_doc.close()
            
            if len(compressed) < original_size:
                print(f"PyMuPDF compression: {original_size} -> {len(compressed)} bytes")
                return compressed
                
        except Exception as e:
            print(f"PyMuPDF compression failed: {e}")
        
        # Method 3: Try chunked processing for very large files
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # For very large files, try processing in chunks
            if doc.page_count > 10:  # If more than 10 pages
                # Process first 10 pages only (usually contains main info)
                new_doc = fitz.open()
                pages_to_process = min(10, doc.page_count)
                
                for page_num in range(pages_to_process):
                    page = doc.load_page(page_num)
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Save with compression
                output = BytesIO()
                new_doc.save(output, garbage=4, deflate=True, clean=True)
                output.seek(0)
                compressed = output.getvalue()
                
                doc.close()
                new_doc.close()
                
                if len(compressed) < original_size:
                    print(f"Chunked compression: {original_size} -> {len(compressed)} bytes")
                    return compressed
                    
        except Exception as e:
            print(f"Chunked compression failed: {e}")
        
        # Method 4: Try reducing image quality if images are the issue
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Check if PDF has many images
            total_images = 0
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                images = page.get_images()
                total_images += len(images)
            
            if total_images > 5:  # If PDF has many images
                # Create new document with reduced image quality
                new_doc = fitz.open()
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Save with image compression
                output = BytesIO()
                new_doc.save(output, 
                            garbage=4, 
                            deflate=True, 
                            clean=True,
                            compress=True)  # Enable image compression
                output.seek(0)
                compressed = output.getvalue()
                
                doc.close()
                new_doc.close()
                
                if len(compressed) < original_size:
                    print(f"Image compression: {original_size} -> {len(compressed)} bytes")
                    return compressed
                    
        except Exception as e:
            print(f"Image compression failed: {e}")
        
        # If all methods fail, return original
        print(f"All compression methods failed, returning original size: {original_size} bytes")
        return pdf_bytes
    
    async def _compress_pdf_fast(self, pdf_bytes: bytes) -> bytes:
        """Fast compression method - quick but moderate reduction"""
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            pdf_writer = PyPDF2.PdfWriter()
            
            for page in pdf_reader.pages:
                page.compress_content_streams()
                pdf_writer.add_page(page)
            
            output = BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            print(f"Fast compression failed: {e}")
            return pdf_bytes
    
    async def _compress_pdf_standard(self, pdf_bytes: bytes) -> bytes:
        """Standard compression method - balanced approach"""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            new_doc = fitz.open()
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            output = BytesIO()
            new_doc.save(output, garbage=3, deflate=True, clean=True)
            output.seek(0)
            compressed = output.getvalue()
            
            doc.close()
            new_doc.close()
            
            return compressed if len(compressed) < len(pdf_bytes) else pdf_bytes
            
        except Exception as e:
            print(f"Standard compression failed: {e}")
            return pdf_bytes
    
    async def _compress_pdf_maximum(self, pdf_bytes: bytes) -> bytes:
        """Maximum compression method - best compression but slower"""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            new_doc = fitz.open()
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            output = BytesIO()
            new_doc.save(output, 
                        garbage=4,           # Maximum garbage collection
                        deflate=True,        # Use deflate compression
                        clean=True,          # Clean unused objects
                        linear=True,         # Linearize for web
                        pretty=False,        # Minimize whitespace
                        ascii=False)         # Use binary for smaller size
            
            output.seek(0)
            compressed = output.getvalue()
            
            doc.close()
            new_doc.close()
            
            return compressed if len(compressed) < len(pdf_bytes) else pdf_bytes
            
        except Exception as e:
            print(f"Maximum compression failed: {e}")
            return pdf_bytes
    
    async def _compress_pdf_images(self, pdf_bytes: bytes) -> bytes:
        """Image-focused compression for photo-heavy PDFs"""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            new_doc = fitz.open()
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            output = BytesIO()
            new_doc.save(output, 
                        garbage=4, 
                        deflate=True, 
                        clean=True,
                        compress=True)  # Enable image compression
            
            output.seek(0)
            compressed = output.getvalue()
            
            doc.close()
            new_doc.close()
            
            return compressed if len(compressed) < len(pdf_bytes) else pdf_bytes
            
        except Exception as e:
            print(f"Image compression failed: {e}")
            return pdf_bytes
    
    async def _compress_pdf_pages(self, pdf_bytes: bytes) -> bytes:
        """Page-limited compression - keep only first 10 pages"""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if doc.page_count <= 10:
                # If 10 or fewer pages, use standard compression
                return await self._compress_pdf_standard(pdf_bytes)
            
            # Keep only first 10 pages
            new_doc = fitz.open()
            pages_to_process = min(10, doc.page_count)
            
            for page_num in range(pages_to_process):
                page = doc.load_page(page_num)
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            output = BytesIO()
            new_doc.save(output, garbage=4, deflate=True, clean=True)
            output.seek(0)
            compressed = output.getvalue()
            
            doc.close()
            new_doc.close()
            
            return compressed if len(compressed) < len(pdf_bytes) else pdf_bytes
            
        except Exception as e:
            print(f"Page compression failed: {e}")
            return pdf_bytes
    
    async def handle_compression_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle compression method selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        compression_type = query.data
        
        # Check if user has a PDF in session
        if not self.user_sessions.get(user_id, {}).get('files', {}).get('pdf'):
            await query.edit_message_text(
                "❌ **No PDF Found**\n\n"
                "You need to upload a PDF first before compressing it.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        pdf_bytes = self.user_sessions[user_id]['files']['pdf']
        original_size = len(pdf_bytes)
        
        # Show compression progress
        await query.edit_message_text(
            "🗜️ **Compressing your PDF...**\n\n"
            f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
            f"📏 **Original Size:** {original_size / (1024*1024):.1f} MB\n\n"
            "⏳ Please wait while I compress your file...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Compress based on selected method
            if compression_type == "compress_fast":
                compressed_bytes = await self._compress_pdf_fast(pdf_bytes)
            elif compression_type == "compress_standard":
                compressed_bytes = await self._compress_pdf_standard(pdf_bytes)
            elif compression_type == "compress_maximum":
                compressed_bytes = await self._compress_pdf_maximum(pdf_bytes)
            elif compression_type == "compress_images":
                compressed_bytes = await self._compress_pdf_images(pdf_bytes)
            elif compression_type == "compress_pages":
                compressed_bytes = await self._compress_pdf_pages(pdf_bytes)
            else:
                compressed_bytes = await self._compress_pdf_bytes(pdf_bytes)
            
            compressed_size = len(compressed_bytes)
            
            if compressed_size < original_size:
                # Update session with compressed PDF
                self.user_sessions[user_id]['files']['pdf'] = compressed_bytes
                
                # Send compressed PDF back
                bio = BytesIO(compressed_bytes)
                bio.name = f"compressed_{self.user_sessions[user_id].get('pdf_filename', 'document.pdf')}"
                
                await context.bot.send_document(
                    chat_id=user_id,
                    document=InputFile(bio, filename=bio.name),
                    caption=(
                        "✅ **PDF Compressed Successfully!**\n\n"
                        f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
                        f"📏 **Original:** {original_size / (1024*1024):.1f} MB\n"
                        f"📏 **Compressed:** {compressed_size / (1024*1024):.1f} MB\n"
                        f"💾 **Saved:** {((original_size - compressed_size) / original_size * 100):.1f}%\n\n"
                        "🔄 **Next:** Try processing the compressed PDF now!"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Update the message to show success
                await query.edit_message_text(
                    "✅ **Compression Complete!**\n\n"
                    f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
                    f"📏 **Original:** {original_size / (1024*1024):.1f} MB\n"
                    f"📏 **Compressed:** {compressed_size / (1024*1024):.1f} MB\n"
                    f"💾 **Saved:** {((original_size - compressed_size) / original_size * 100):.1f}%\n\n"
                    "📤 **Compressed file sent above!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            else:
                await query.edit_message_text(
                    "⚠️ **Compression Unsuccessful**\n\n"
                    f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
                    f"📏 **Size:** {original_size / (1024*1024):.1f} MB\n\n"
                    "💡 **The file couldn't be compressed further.**\n"
                    "Try sending a PDF link instead.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            await query.edit_message_text(
                "❌ **Compression Failed**\n\n"
                f"📁 **File:** `{self.user_sessions[user_id].get('pdf_filename', 'Unknown')}`\n"
                f"📏 **Size:** {original_size / (1024*1024):.1f} MB\n\n"
                "🔧 **Error:** Compression process failed\n\n"
                "💡 **Alternatives:**\n"
                "• Send PDF link (Google Drive)\n"
                "• Use online compressors\n"
                "• Split the PDF",
                parse_mode=ParseMode.MARKDOWN
            )

    def run(self):
        # Configure application with proper timeout settings
        application = (
            Application.builder()
            .token(self.token)
            .read_timeout(60)  # 60 seconds read timeout
            .write_timeout(60)  # 60 seconds write timeout
            .connect_timeout(30)  # 30 seconds connection timeout
            .pool_timeout(60)  # 60 seconds pool timeout
            .build()
        )
        
        # Set up conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start),
                # Allow users to send a PDF immediately without /start
                MessageHandler(filters.Document.ALL, self.receive_pdf),
                # Fallback: auto-start on any other message
                MessageHandler(filters.ALL, self.auto_start)
            ],
            states={
                WAITING_FOR_LANGUAGE: [
                    CallbackQueryHandler(self.handle_language_choice, pattern="^lang_"),
                ],
                WAITING_FOR_UNAUTHORIZED_LANGUAGE: [
                    CallbackQueryHandler(self.handle_unauthorized_language_choice, pattern="^unauthorized_lang_"),
                ],
                WAITING_FOR_PDF: [
                    MessageHandler(filters.Document.ALL, self.receive_pdf),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_wrong_input_pdf),
                    MessageHandler(filters.PHOTO, self.handle_wrong_input_pdf),
                    MessageHandler(filters.VIDEO, self.handle_wrong_input_pdf),
                    MessageHandler(filters.AUDIO, self.handle_wrong_input_pdf),
                    MessageHandler(filters.VOICE, self.handle_wrong_input_pdf)
                ],
                WAITING_FOR_FIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_fin),
                    MessageHandler(filters.Document.ALL, self.handle_wrong_input_fin),
                    MessageHandler(filters.PHOTO, self.handle_wrong_input_fin),
                    MessageHandler(filters.VIDEO, self.handle_wrong_input_fin),
                    MessageHandler(filters.AUDIO, self.handle_wrong_input_fin),
                    MessageHandler(filters.VOICE, self.handle_wrong_input_fin)
                ],
                CONFIRMING_DATA: [
                    CallbackQueryHandler(self.handle_data_preview_choice, pattern="^data_"),
                    CallbackQueryHandler(self.handle_edit_choice, pattern="^(edit_personal|edit_address|edit_nationality|edit_options|generate)$"),
                    CallbackQueryHandler(self.handle_settings_choice, pattern="^settings_"),
                    CallbackQueryHandler(self.handle_mode_choice, pattern="^mode_"),
                    CallbackQueryHandler(self.handle_language_choice, pattern="^lang_"),
                    CallbackQueryHandler(self.handle_bg_option, pattern="^bg_"),
                    CallbackQueryHandler(self.handle_id_type, pattern="^id_"),
                    CallbackQueryHandler(self.handle_output_variant, pattern="^variant_"),
                    CallbackQueryHandler(self.handle_city_type, pattern="^city_"),
                    CallbackQueryHandler(self.handle_field_edit, pattern="^edit_(?!personal$|address$|nationality$|options$).+"),
                    CallbackQueryHandler(self.handle_photo_choice, pattern="^photo_"),
                    CallbackQueryHandler(self.handle_compression_choice, pattern="^compress_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_field_value)
                ],
                WAITING_FOR_PHOTO: [
                    CallbackQueryHandler(self.handle_photo_choice, pattern="^photo_"),
                    MessageHandler(filters.PHOTO, self.receive_photo),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_photo),
                    MessageHandler(filters.Document.ALL, self.receive_photo),
                    MessageHandler(filters.VIDEO, self.receive_photo),
                    MessageHandler(filters.AUDIO, self.receive_photo),
                    MessageHandler(filters.VOICE, self.receive_photo)
                ],
                WAITING_FOR_FIELD_VALUE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_field_value)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel), CommandHandler("help", self.help_command)]
        )
        application.add_handler(conv_handler)
        # Add quick settings handler outside conversation
        application.add_handler(CallbackQueryHandler(self.handle_quick_settings, pattern="^quick_"))
        # Add settings menu handlers outside conversation
        application.add_handler(CallbackQueryHandler(self.handle_settings_choice, pattern="^settings_"))
        application.add_handler(CallbackQueryHandler(self.handle_mode_choice, pattern="^mode_"))
        application.add_handler(CallbackQueryHandler(self.handle_language_choice, pattern="^lang_"))
        # Add all other settings handlers (mapped to their specific callbacks)
        application.add_handler(CallbackQueryHandler(self.handle_bg_option, pattern="^bg_"))
        application.add_handler(CallbackQueryHandler(self.handle_id_type, pattern="^id_"))
        application.add_handler(CallbackQueryHandler(self.handle_output_variant, pattern="^variant_"))
        application.add_handler(CallbackQueryHandler(self.handle_city_type, pattern="^city_"))
        application.add_handler(CallbackQueryHandler(self.handle_data_preview_choice, pattern="^data_"))
        application.add_handler(CallbackQueryHandler(self.handle_settings_choice, pattern="^back_to_start"))
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('cancel', self.cancel))
        application.add_handler(CommandHandler('compress', self.compress_pdf))
        application.add_handler(CommandHandler('report', self.daily_report_command))
        print("Starting Fyda Telegram Bot...")
        if self.restrict_access:
            # Merge file-based allowlist if available
            try:
                # Direct file reading instead of importing allowlist_store
                allowlist_path = os.path.join(os.path.dirname(__file__), 'data', 'allowed_users.json')
                if os.path.exists(allowlist_path):
                    with open(allowlist_path, 'r', encoding='utf-8') as f:
                        file_ids = json.load(f)
                    if isinstance(file_ids, list):
                        dynamic_ids = []
                        for item in file_ids:
                            try:
                                dynamic_ids.append(int(item))
                            except (ValueError, TypeError):
                                continue
                if dynamic_ids:
                    self.allowed_user_ids = sorted(set([*self.allowed_user_ids, *dynamic_ids]))
                # Always restrict access when using allowlist (even if empty)
                self.restrict_access = True
            except Exception:
                pass
            print(f"Access restricted to {len(self.allowed_user_ids)} authorized users")
        else:
            print("Access open to all users")
        application.run_polling()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        print("Please set your Telegram bot token in a .env file or environment variable.")
        sys.exit(1)

    # Parse optional ALLOWED_USER_IDS from environment (comma-separated integers)
    allowed_user_ids_env = os.getenv('ALLOWED_USER_IDS', '')
    allowed_user_ids: list[int] = []
    if allowed_user_ids_env:
        try:
            allowed_user_ids = [int(uid.strip()) for uid in allowed_user_ids_env.split(',') if uid.strip()]
        except ValueError as e:
            print(f"❌ Error parsing ALLOWED_USER_IDS: {e}")
            print("Please use comma-separated integers, e.g. '123456789,987654321'")
            allowed_user_ids = []

    bot = FydaTelegramBot(BOT_TOKEN, allowed_user_ids=allowed_user_ids)
    bot.run()