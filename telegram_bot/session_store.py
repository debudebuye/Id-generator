"""Per-user Telegram bot session state.

The bot's multi-step flow (upload PDF -> FIN -> preview/edit -> generate) used to
keep this in a plain in-memory dict (`FydaTelegramBot.sessions`). That only works
when one long-running process handles every message via polling. On Cloud Run the
process can be recycled or scaled to multiple instances between two messages from
the same user, so the state has to live somewhere all instances can reach -
Firestore, same project the rest of the app already uses via `firebase_service`.

Falls back to a local JSON file when Firestore isn't configured, so local
development/polling still works without any Firebase setup. The local fallback is
only correct for a single process - it exists for dev convenience, not as a
second production backend.
"""
import os
import json
from typing import Dict, Optional

from app.services.firebase_service import firebase_service

_COLLECTION = 'bot_sessions'
_LOCAL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'bot_sessions_local.json')


class SessionStore:
    def __init__(self):
        self.db = firebase_service.db

    def load(self, user_id: int) -> Optional[Dict]:
        if self.db is not None:
            try:
                doc = self.db.collection(_COLLECTION).document(str(user_id)).get()
                return doc.to_dict() if doc.exists else None
            except Exception as e:
                print(f"⚠️ SessionStore.load (Firestore) failed, falling back to local: {e}")
        return self._load_local().get(user_id)

    def save(self, user_id: int, session: Dict) -> None:
        if self.db is not None:
            try:
                self.db.collection(_COLLECTION).document(str(user_id)).set(session)
                return
            except Exception as e:
                print(f"⚠️ SessionStore.save (Firestore) failed, falling back to local: {e}")
        data = self._load_local()
        data[user_id] = session
        self._save_local(data)

    def delete(self, user_id: int) -> None:
        if self.db is not None:
            try:
                self.db.collection(_COLLECTION).document(str(user_id)).delete()
                return
            except Exception as e:
                print(f"⚠️ SessionStore.delete (Firestore) failed, falling back to local: {e}")
        data = self._load_local()
        data.pop(user_id, None)
        self._save_local(data)

    # ── Local JSON fallback (dev only) ──────────────────────────────────────
    def _load_local(self) -> Dict[int, Dict]:
        try:
            if os.path.exists(_LOCAL_PATH):
                with open(_LOCAL_PATH, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                return {int(k): v for k, v in raw.items()}
        except Exception:
            pass
        return {}

    def _save_local(self, data: Dict[int, Dict]) -> None:
        try:
            os.makedirs(os.path.dirname(_LOCAL_PATH), exist_ok=True)
            with open(_LOCAL_PATH, 'w', encoding='utf-8') as f:
                json.dump({str(k): v for k, v in data.items()}, f, ensure_ascii=False)
        except Exception:
            pass
