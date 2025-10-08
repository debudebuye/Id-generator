#!/usr/bin/env python3
"""
Persistent allowlist management for Telegram user IDs.

Stores a JSON file with a list of integers. Creates the file if missing.
"""

import json
import os
from pathlib import Path
from typing import List


DEFAULT_DATA_DIR = Path("data")
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_ALLOWLIST_PATH = DEFAULT_DATA_DIR / "allowed_users.json"


def _ensure_file(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")


def read_allowlist(path: Path = DEFAULT_ALLOWLIST_PATH) -> List[int]:
    """Read allowed user IDs from JSON file; returns empty list if missing/invalid."""
    try:
        _ensure_file(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            result: List[int] = []
            for item in data:
                try:
                    result.append(int(item))
                except Exception:
                    # skip non-integer entries
                    continue
            return sorted(set(result))
    except Exception:
        pass
    return []


def write_allowlist(user_ids: List[int], path: Path = DEFAULT_ALLOWLIST_PATH) -> None:
    """Write allowed user IDs to JSON file (unique, sorted)."""
    unique_sorted = sorted(set(int(uid) for uid in user_ids))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(unique_sorted, ensure_ascii=False, indent=2), encoding="utf-8")


def add_user(user_id: int, path: Path = DEFAULT_ALLOWLIST_PATH) -> List[int]:
    ids = read_allowlist(path)
    ids.append(int(user_id))
    write_allowlist(ids, path)
    return read_allowlist(path)


def remove_user(user_id: int, path: Path = DEFAULT_ALLOWLIST_PATH) -> List[int]:
    ids = read_allowlist(path)
    remaining = [int(x) for x in ids if int(x) != int(user_id)]
    write_allowlist(remaining, path)
    return read_allowlist(path)


