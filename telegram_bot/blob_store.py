"""Storage for the one piece of session state too big for a Firestore document:
the uploaded PDF (up to 25 MB), kept only for the brief gap between "PDF received"
and "FIN received" when the FIN wasn't auto-detected.

Uses Firebase Storage (same Firebase project as everything else) so any Cloud Run
instance can load a blob saved by a different instance. Falls back to a local temp
directory when Storage isn't configured (dev only - not valid across instances).
"""
import os
import uuid
from typing import Optional

try:
    from firebase_admin import storage as fb_storage
except ImportError:
    fb_storage = None

_LOCAL_DIR = os.path.join(os.path.dirname(__file__), 'data', 'blobs')


def _bucket():
    if fb_storage is None:
        return None
    try:
        return fb_storage.bucket()
    except Exception:
        return None


def save_pdf(user_id: int, data: bytes) -> str:
    """Stores `data` and returns an opaque ref to pass through session state."""
    key = f"bot_uploads/{user_id}/{uuid.uuid4().hex}.pdf"
    bucket = _bucket()
    if bucket is not None:
        try:
            blob = bucket.blob(key)
            blob.upload_from_string(data, content_type='application/pdf')
            return key
        except Exception as e:
            print(f"⚠️ blob_store.save_pdf (Storage) failed, falling back to local disk: {e}")

    os.makedirs(_LOCAL_DIR, exist_ok=True)
    local_path = os.path.join(_LOCAL_DIR, key.replace('/', '_'))
    with open(local_path, 'wb') as f:
        f.write(data)
    return f"local:{local_path}"


def load_pdf(ref: Optional[str]) -> Optional[bytes]:
    if not ref:
        return None
    if ref.startswith('local:'):
        path = ref[len('local:'):]
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return f.read()
        return None

    bucket = _bucket()
    if bucket is None:
        return None
    try:
        blob = bucket.blob(ref)
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    except Exception as e:
        print(f"⚠️ blob_store.load_pdf (Storage) failed: {e}")
        return None


def delete_pdf(ref: Optional[str]) -> None:
    if not ref:
        return
    if ref.startswith('local:'):
        path = ref[len('local:'):]
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        return

    bucket = _bucket()
    if bucket is None:
        return
    try:
        bucket.blob(ref).delete()
    except Exception:
        pass
