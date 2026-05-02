import os
import json
import threading
import time
from typing import Any, Optional

class DiskCache:
    """
    A simple persistent JSON cache with thread-safety.
    """
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self._lock = threading.RLock()
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        # Sanitize key for filesystem
        safe_key = "".join([c if c.isalnum() or c in "._-" else "_" for c in str(key)])
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        with self._lock:
            if not os.path.exists(path):
                return None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"DiskCache Error reading {key}: {e}")
                return None

    def set(self, key: str, value: Any):
        path = self._get_path(key)
        with self._lock:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False)
            except Exception as e:
                print(f"DiskCache Error writing {key}: {e}")

    def has(self, key: str) -> bool:
        return os.path.exists(self._get_path(key))
