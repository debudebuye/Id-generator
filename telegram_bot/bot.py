import os
import sys
import re
import json
import asyncio
from io import BytesIO
from typing import Dict, Any, List, Optional

import requests
import pytz
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
from telegram.constants import ParseMode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.id_card_service import IDCardService
from app.services.daily_report_service import DailyReportService
from app.services.firebase_service import firebase_service

# ── Conversation states ────────────────────────────────────────────────────────
WAITING_FOR_PDF   = 1
WAITING_FOR_FIN   = 2
CONFIRMING_DATA   = 3
WAITING_FOR_PHOTO = 4
WAITING_FOR_FIELD = 5

# ── Editable fields ────────────────────────────────────────────────────────────
EDITABLE_FIELDS = [
    'name_en', 'name_am', 'gender_en', 'gender_am',
    'dob_en', 'dob_am', 'nationality_en', 'nationality_am',
    'region_en', 'region_am', 'subcity_en', 'subcity_am',
    'woreda_en', 'woreda_am', 'phone'
]

# ── Address helper: only builds combined address strings, never cleans extracted fields
def _apply_smart_address(data: dict) -> None:
    for lang in ['en', 'am']:
        parts = [
            data.get(f'region_{lang}', ''),
            data.get(f'subcity_{lang}', ''),
            data.get(f'woreda_{lang}', '')
        ]
        parts = [p.strip() for p in parts if p and p.strip()]
        if parts:
            data[f'address_{lang}'] = ', '.join(parts)


# ── Bot class ──────────────────────────────────────────────────────────────────
class FydaTelegramBot:
    def __init__(self, token: str, allowed_user_ids: List[int] = None):
        self.token = token
        self.id_service = IDCardService()
        self.daily_service = DailyReportService()
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.allowed_user_ids: List[int] = allowed_user_ids or []
        self._env_allowed_ids: List[int] = list(self.allowed_user_ids)  # keep env IDs permanently
        self.restrict_access = allowed_user_ids is not None
        self.admin_ids: List[int] = []
        self._recently_notified: Dict[int, float] = {}
        self.ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')

        prefs_file = os.path.join(os.path.dirname(__file__), 'data', 'user_preferences.json')
        self.prefs_file = prefs_file
        self.user_prefs: Dict[int, Dict] = self._load_json(prefs_file, {})

        try:
            env_ids = os.getenv('ADMIN_USER_IDS', '')
            if env_ids:
                self.admin_ids = [int(x.strip()) for x in env_ids.split(',') if x.strip()]
        except Exception:
            pass

    # ── Persistence helpers ────────────────────────────────────────────────────
    def _load_json(self, path: str, default):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    return {int(k): v for k, v in raw.items()}
                return raw
        except Exception:
            pass
        return default

    def _save_json(self, path: str, data) -> None:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            serialisable = {str(k): v for k, v in data.items()} if isinstance(data, dict) else data
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(serialisable, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Access control ─────────────────────────────────────────────────────────
    def _refresh_allowlist(self) -> None:
        path = os.path.join(os.path.dirname(__file__), 'data', 'allowed_users.json')
        try:
            file_ids: set = set()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    ids = json.load(f)
                file_ids = {int(i) for i in ids if str(i).isdigit()}
            # Always merge env IDs + file IDs
            self.allowed_user_ids = sorted(set(self._env_allowed_ids) | file_ids)
            self.restrict_access = True
        except Exception:
            # On any error, at least keep env IDs
            self.allowed_user_ids = sorted(set(self._env_allowed_ids))
            self.restrict_access = True

    def is_authorized(self, user_id: int) -> bool:
        if not self.restrict_access:
            return True
        self._refresh_allowlist()
        if user_id in self.allowed_user_ids:
            return True
        try:
            ud = firebase_service.get_user_data(str(user_id))
            return ud and ud.get('access_status') == 'approved'
        except Exception:
            return False

    def is_paused(self) -> bool:
        return self.daily_service.is_bot_paused()

    def is_user_paused(self, user_id: int) -> bool:
        return self.daily_service.is_user_paused(user_id)

    # ── Session helpers ────────────────────────────────────────────────────────
    def _new_session(self, user_id: int) -> Dict:
        self.sessions[user_id] = {'data': {}, 'pdf': None, 'edit_field': None}
        return self.sessions[user_id]

    def _session(self, user_id: int) -> Dict:
        return self.sessions.get(user_id) or self._new_session(user_id)

    # ── Admin notification ─────────────────────────────────────────────────────
    async def _notify_admins(self, context, user_id: int, name: str, username: str) -> None:
        import time
        now = time.time()
        if now - self._recently_notified.get(user_id, 0) < 30:
            return
        self._recently_notified[user_id] = now
        self._recently_notified = {k: v for k, v in self._recently_notified.items() if now - v < 300}
        try:
            payload = {
                'id': str(user_id), 'telegramId': str(user_id),
                'username': username, 'firstName': name,
                'lastName': '', 'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': 'pending'
            }
            url = os.getenv('ADMIN_BACKEND_URL', 'http://localhost:5000')
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, lambda: requests.post(f'{url}/api/new-users', json=payload, timeout=5))
        except Exception:
            pass

    async def _ensure_firebase_user(self, user_id: int, name: str, username: str) -> None:
        try:
            existing = firebase_service.get_user_data(str(user_id))
            data = {
                'telegramId': str(user_id), 'firstName': name,
                'username': username, 'lastActivity': datetime.utcnow().isoformat() + 'Z',
                'access_status': existing.get('access_status', 'not approved') if existing else 'not approved',
                'today_ids': existing.get('today_ids', 0) if existing else 0,
                'total_ids': existing.get('total_ids', 0) if existing else 0,
            }
            firebase_service.create_or_update_user(data)
        except Exception:
            pass

    # ── /start ─────────────────────────────────────────────────────────────────
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        name = update.effective_user.first_name or 'User'
        username = update.effective_user.username or ''

        if self.is_paused():
            await update.message.reply_text("⏸ Bot is paused. Please wait.")
            return ConversationHandler.END

        await self._ensure_firebase_user(user_id, name, username)

        if not self.is_authorized(user_id):
            await self._notify_admins(context, user_id, name, username)
            admin = os.getenv('ADMIN_CONTACT', '@fayda_software').replace('_', '\\_')
            await update.message.reply_text(
                f"🚫 *Access Denied*\n\nContact {admin} to get access.\n\nYour ID: `{user_id}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END

        if self.is_user_paused(user_id):
            await update.message.reply_text("⏸ Your account is paused. Contact @fayda\\_software.")
            return ConversationHandler.END

        self._new_session(user_id)
        stats = self.daily_service.get_user_stats(user_id)
        today = stats.get('today_count', 0)
        unpaid = stats.get('total_unpaid', 0)

        text = (
            f"🇪🇹 *Ethiopian Digital ID Bot*\n\n"
            f"Hello {name}!\n\n"
            f"📄 Upload your PDF to get started."
        )
        if today > 0:
            text += f"\n\n📊 Today: {today} IDs | Unpaid: {unpaid}"

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return WAITING_FOR_PDF

    async def auto_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return await self.start(update, context)

    # ── /cancel ────────────────────────────────────────────────────────────────
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.sessions.pop(update.effective_user.id, None)
        await update.message.reply_text("❌ Cancelled. Send /start to begin again.")
        return ConversationHandler.END

    # ── /report ────────────────────────────────────────────────────────────────
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access denied.")
            return ConversationHandler.END
        stats = self.daily_service.get_user_stats(user_id)
        today = stats.get('today_count', 0)
        unpaid = stats.get('total_unpaid', 0)
        await update.message.reply_text(
            f"📊 *Your Stats*\n\n✅ Today: {today}\n📈 Unpaid: {unpaid}",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    # ── Receive PDF ────────────────────────────────────────────────────────────
    async def receive_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id

        if self.is_paused():
            await update.message.reply_text("⏸ Bot is paused.")
            return ConversationHandler.END
        if not self.is_authorized(user_id):
            await update.message.reply_text(f"🚫 Access denied. Your ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        if self.is_user_paused(user_id):
            await update.message.reply_text("⏸ Your account is paused.")
            return ConversationHandler.END

        doc = update.message.document
        if not doc or not doc.file_name.lower().endswith('.pdf'):
            await update.message.reply_text("📄 Please send a PDF file.")
            return WAITING_FOR_PDF

        if doc.file_size and doc.file_size > 25 * 1024 * 1024:
            await update.message.reply_text("❌ File too large (max 25 MB).")
            return WAITING_FOR_PDF

        await update.message.reply_text("⏳ Processing your PDF...")

        try:
            file = await context.bot.get_file(doc.file_id)
            pdf_bytes = bytes(await file.download_as_bytearray())
        except Exception as e:
            await update.message.reply_text(f"❌ Download failed: {e}")
            return WAITING_FOR_PDF

        session = self._new_session(user_id)
        session['pdf'] = pdf_bytes
        session['pdf_name'] = doc.file_name

        # Try auto-extract FIN
        try:
            auto_fin = self.id_service.extract_fin_from_pdf(BytesIO(pdf_bytes))
        except Exception:
            auto_fin = None

        if auto_fin:
            session['data']['fin'] = auto_fin
            return await self._extract_and_preview(update, context, user_id, pdf_bytes, auto_fin)
        else:
            await update.message.reply_text("✅ PDF received.\n\nPlease send your 12-digit FIN number.")
            return WAITING_FOR_FIN

    # ── Receive FIN ────────────────────────────────────────────────────────────
    async def receive_fin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access denied.")
            return ConversationHandler.END

        raw = update.message.text.strip()
        fin = re.sub(r'[\s_\-.,a-zA-Z]', '', raw)

        if not fin.isdigit() or len(fin) != 12:
            await update.message.reply_text(
                f"❌ Invalid FIN: `{fin}`\n\nSend exactly 12 digits.",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIN

        session = self._session(user_id)
        pdf_bytes = session.get('pdf')
        if not pdf_bytes:
            await update.message.reply_text("❌ No PDF found. Please upload your PDF first.")
            return WAITING_FOR_PDF

        session['data']['fin'] = fin
        return await self._extract_and_preview(update, context, user_id, pdf_bytes, fin)

    # ── Core: extract data then show preview ───────────────────────────────────
    async def _extract_and_preview(self, update, context, user_id: int,
                                   pdf_bytes: bytes, fin: str) -> int:
        try:
            extracted = self.id_service.extract_pdf_data(BytesIO(pdf_bytes), fin, 'auto')
        except Exception as e:
            await update.message.reply_text(f"❌ Extraction failed: {e}\n\nTry uploading the PDF again.")
            return WAITING_FOR_PDF

        session = self._session(user_id)
        session['data'].update(extracted)
        data = session['data']

        # Smart address formatting
        _apply_smart_address(data)

        # Defaults
        data.setdefault('remove_white_bg', False)
        data.setdefault('id_type', 'normal')
        data.setdefault('output_variant', 'reverse')

        # Auto-detect city format: same logic as web (subcity_en > 30 chars → 'shger')
        subcity_en = data.get('subcity_en', '')
        data['city_type'] = 'shger' if len(subcity_en) > 30 else 'default'

        await self._send_preview(update, context, user_id)
        return CONFIRMING_DATA

    # ── Send preview message ───────────────────────────────────────────────────
    async def _send_preview(self, update, context, user_id: int) -> None:
        data = self._session(user_id)['data']
        nf = 'N/A'

        lines = [
            f"📋 *Extracted Data*\n",
            f"👤 *{data.get('name_en', nf)}* | {data.get('name_am', nf)}",
            f"🔢 FIN: `{data.get('fin', nf)}`",
            f"⚧ {data.get('gender_en', nf)} | DOB: {data.get('dob_en', nf)}",
            f"🌍 {data.get('nationality_en', nf)}",
            f"📍 {data.get('address_en', nf)}",
            f"📞 {data.get('phone', nf)}",
        ]
        text = '\n'.join(lines)

        bg_on = data.get('remove_white_bg', False)
        bg_btn = "🖼 BG Remove: ON" if bg_on else "🚫 BG Remove: OFF"

        keyboard = [
            [InlineKeyboardButton(bg_btn, callback_data="toggle_bg")],
            [InlineKeyboardButton("✏️ Edit Field", callback_data="edit_menu"),
             InlineKeyboardButton("🔁 Replace Photo", callback_data="photo_replace")],
            [InlineKeyboardButton("🚀 Generate ID", callback_data="generate")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]

        # Send photo preview if available
        photo_path = data.get('photo')
        photo_bytes = data.get('photo_bytes')
        if photo_bytes:
            try:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=BytesIO(photo_bytes),
                    caption="📸 Photo preview"
                )
            except Exception:
                pass
        elif photo_path:
            abs_path = os.path.join(self.id_service.config.STATIC_FOLDER, os.path.basename(photo_path))
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'rb') as f:
                        await context.bot.send_photo(
                            chat_id=user_id, photo=f,
                            caption="📸 Extracted photo"
                        )
                except Exception:
                    pass

        # Send data preview with action buttons
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await context.bot.send_message(
                chat_id=user_id, text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # ── Callback handler ───────────────────────────────────────────────────────
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        choice = query.data

        if not self.is_authorized(user_id):
            await query.edit_message_text("🚫 Access denied.")
            return ConversationHandler.END

        session = self._session(user_id)
        data = session['data']

        # ── Toggle BG removal ──────────────────────────────────────────────────
        if choice == 'toggle_bg':
            data['remove_white_bg'] = not data.get('remove_white_bg', False)
            bg_on = data['remove_white_bg']
            bg_btn = "🖼 BG Remove: ON" if bg_on else "🚫 BG Remove: OFF"
            keyboard = [
                [InlineKeyboardButton(bg_btn, callback_data="toggle_bg")],
                [InlineKeyboardButton("✏️ Edit Field", callback_data="edit_menu"),
                 InlineKeyboardButton("🔁 Replace Photo", callback_data="photo_replace")],
                [InlineKeyboardButton("🚀 Generate ID", callback_data="generate")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            try:
                await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
            except Exception:
                pass
            return CONFIRMING_DATA

        # ── Generate ───────────────────────────────────────────────────────────
        elif choice == 'generate':
            await query.edit_message_text("🔄 Generating your ID...")
            await self._generate(context, user_id)
            return ConversationHandler.END

        # ── Edit menu ──────────────────────────────────────────────────────────
        elif choice == 'edit_menu':
            keyboard = []
            labels = {
                'name_en': 'Name (EN)', 'name_am': 'Name (AM)',
                'gender_en': 'Gender (EN)', 'gender_am': 'Gender (AM)',
                'dob_en': 'DOB (EN)', 'dob_am': 'DOB (AM)',
                'nationality_en': 'Nationality (EN)', 'nationality_am': 'Nationality (AM)',
                'region_en': 'Region (EN)', 'region_am': 'Region (AM)',
                'subcity_en': 'Subcity (EN)', 'subcity_am': 'Subcity (AM)',
                'woreda_en': 'Woreda (EN)', 'woreda_am': 'Woreda (AM)',
                'phone': 'Phone'
            }
            row = []
            for field, label in labels.items():
                row.append(InlineKeyboardButton(label, callback_data=f"ef_{field}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_preview")])
            await query.edit_message_text("✏️ *Select field to edit:*",
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=InlineKeyboardMarkup(keyboard))
            return CONFIRMING_DATA

        # ── Edit specific field ────────────────────────────────────────────────
        elif choice.startswith('ef_'):
            field = choice[3:]
            session['edit_field'] = field
            current = data.get(field, '')
            await query.edit_message_text(
                f"✏️ *{field}*\nCurrent: `{current}`\n\nSend new value:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_FIELD

        # ── Back to preview ────────────────────────────────────────────────────
        elif choice == 'back_preview':
            await query.delete_message()
            await self._send_preview(update, context, user_id)
            return CONFIRMING_DATA

        # ── Replace photo ──────────────────────────────────────────────────────
        elif choice == 'photo_replace':
            await query.edit_message_text("📸 Send your photo (as image or PNG document).")
            return WAITING_FOR_PHOTO

        # ── Cancel ─────────────────────────────────────────────────────────────
        elif choice == 'cancel':
            self.sessions.pop(user_id, None)
            await query.edit_message_text("❌ Cancelled.")
            return ConversationHandler.END

        return CONFIRMING_DATA

    # ── Receive edited field value ─────────────────────────────────────────────
    async def receive_field_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        session = self._session(user_id)
        field = session.get('edit_field')
        if not field:
            return CONFIRMING_DATA

        value = update.message.text.strip()
        session['data'][field] = value

        # Rebuild address if address component changed
        if field in ['region_en', 'region_am', 'subcity_en', 'subcity_am', 'woreda_en', 'woreda_am']:
            _apply_smart_address(session['data'])
            # Re-detect city format after edit
            subcity_en = session['data'].get('subcity_en', '')
            session['data']['city_type'] = 'shger' if len(subcity_en) > 30 else 'default'

        session['edit_field'] = None
        await update.message.reply_text(f"✅ `{field}` updated.", parse_mode=ParseMode.MARKDOWN)
        await self._send_preview(update, context, user_id)
        return CONFIRMING_DATA

    # ── Receive replacement photo ──────────────────────────────────────────────
    async def receive_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        session = self._session(user_id)

        try:
            from PIL import Image

            if update.message.document:
                f = await context.bot.get_file(update.message.document.file_id)
            elif update.message.photo:
                f = await context.bot.get_file(update.message.photo[-1].file_id)
            else:
                await update.message.reply_text("📸 Please send a photo or PNG document.")
                return WAITING_FOR_PHOTO

            raw = bytes(await f.download_as_bytearray())
            img = Image.open(BytesIO(raw)).convert('RGBA')

            # Save to the exact filename the service uses as its default
            photo_temp = os.path.join(self.id_service.config.STATIC_FOLDER, 'photo_temp.png')
            img.save(photo_temp, format='PNG')

            # Also store raw bytes in data so get_photo_data() picks it up directly
            buf = BytesIO()
            img.save(buf, format='PNG')
            session['data']['photo_bytes'] = buf.getvalue()
            # Clear any old photo path so the service uses photo_bytes
            session['data'].pop('photo', None)

            await update.message.reply_text("✅ Photo updated.")
            await self._send_preview(update, context, user_id)
            return CONFIRMING_DATA

        except Exception as e:
            await update.message.reply_text(f"❌ Photo error: {e}")
            return WAITING_FOR_PHOTO

    # ── Generate ID card ───────────────────────────────────────────────────────
    async def _generate(self, context, user_id: int) -> None:
        session = self._session(user_id)
        data = session['data']
        user_name = context.bot.username or 'User'

        remove_white = data.get('remove_white_bg', False)
        city_type = data.get('city_type', 'default')
        generate_old = data.get('generate_old_id', False)
        generate_mini = data.get('generate_mini_id', False)
        variant = data.get('output_variant', 'reverse')

        # Ensure address is formatted
        _apply_smart_address(data)

        try:
            loop = asyncio.get_event_loop()
            generated = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.id_service.generate_id_card(
                        data,
                        city_option=city_type,
                        remove_white=remove_white,
                        remove_black=False,
                        generate_front_only=False,
                        generate_reverse_only=(not generate_old and not generate_mini),
                        generate_old_id=generate_old,
                        generate_mini_id=generate_mini
                    )
                ),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            await context.bot.send_message(chat_id=user_id, text="⏰ Timed out. Please try again.")
            return
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text=f"❌ Generation error: {e}")
            return

        # Determine which two files to send (color + grayscale reverse)
        if generate_old:
            to_send = ['old_reverse_color', 'old_reverse_bw']
        elif generate_mini:
            to_send = ['mini_front_color', 'mini_front_bw']
        else:
            to_send = ['reverse', 'reverse_bw']

        sent = 0
        for key in to_send:
            filename = generated.get(key)
            if not filename:
                continue
            path = os.path.join(self.id_service.config.STATIC_FOLDER, filename)
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'rb') as img_file:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=InputFile(img_file, filename=filename)
                    )
                sent += 1
            except Exception as e:
                await context.bot.send_message(chat_id=user_id, text=f"❌ Send error: {e}")

        if sent == 0:
            await context.bot.send_message(chat_id=user_id, text="❌ No output files generated.")
            return

        # Track stats
        try:
            stats = self.daily_service.increment_id_count(user_id, data.get('name_en', 'User'))
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Done!\n\n📊 Today: {stats['today_count']} | Unpaid: {stats['total_unpaid']}\n\nSend a new PDF to start again.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await context.bot.send_message(chat_id=user_id, text="🎉 ID generated! Send a new PDF to start again.")

        # Clear session but keep user in sessions dict
        self.sessions.pop(user_id, None)

    # ── Wrong input helpers ────────────────────────────────────────────────────
    async def wrong_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Generic wrong-input handler — just nudge the user."""
        state = context.user_data.get('_state', WAITING_FOR_PDF)
        if state == WAITING_FOR_FIN:
            await update.message.reply_text("Please send your 12-digit FIN number as text.")
            return WAITING_FOR_FIN
        await update.message.reply_text("📄 Please send a PDF file.")
        return WAITING_FOR_PDF

    # ── Run ────────────────────────────────────────────────────────────────────
    def run(self):
        app = (
            Application.builder()
            .token(self.token)
            .read_timeout(60).write_timeout(60)
            .connect_timeout(30).pool_timeout(60)
            .build()
        )

        conv = ConversationHandler(
            entry_points=[
                CommandHandler('start', self.start),
                MessageHandler(filters.ALL & ~filters.COMMAND, self.auto_start),
            ],
            states={
                WAITING_FOR_PDF: [
                    MessageHandler(filters.Document.ALL, self.receive_pdf),
                    MessageHandler(filters.PHOTO, self.wrong_input),
                    MessageHandler(filters.ALL & ~filters.COMMAND, self.wrong_input),
                ],
                WAITING_FOR_FIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_fin),
                    MessageHandler(filters.ALL & ~filters.COMMAND, self.wrong_input),
                ],
                CONFIRMING_DATA: [
                    CallbackQueryHandler(self.handle_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_field_value),
                ],
                WAITING_FOR_PHOTO: [
                    MessageHandler(filters.PHOTO, self.receive_photo),
                    MessageHandler(filters.Document.ALL, self.receive_photo),
                    MessageHandler(filters.ALL & ~filters.COMMAND, self.receive_photo),
                ],
                WAITING_FOR_FIELD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_field_value),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel),
                CommandHandler('start', self.start),
            ],
            allow_reentry=False,
        )

        app.add_handler(conv)
        app.add_handler(CommandHandler('report', self.report))
        app.add_handler(CommandHandler('cancel', self.cancel))
        app.add_handler(CommandHandler('help', self._help))

        # Merge file-based allowlist
        self._refresh_allowlist()
        print(f"🤖 Bot starting — {len(self.allowed_user_ids)} authorised users")
        app.run_polling()

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            "🇪🇹 *Ethiopian Digital ID Bot*\n\n"
            "1️⃣ Upload your PDF\n"
            "2️⃣ Send FIN if not auto-detected\n"
            "3️⃣ Review data & generate\n\n"
            "/cancel — cancel session\n"
            "/report — your stats",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set.")
        sys.exit(1)

    raw_ids = os.getenv('ALLOWED_USER_IDS', '')
    allowed: List[int] = []
    if raw_ids:
        try:
            allowed = [int(x.strip()) for x in raw_ids.split(',') if x.strip()]
        except ValueError:
            pass

    FydaTelegramBot(TOKEN, allowed_user_ids=allowed).run()
