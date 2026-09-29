import json
import os
from pathlib import Path
from threading import Lock

STORE = Path(os.getenv("PREFS_STORE", "prefs.json"))
_lock = Lock()


def _load() -> dict:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    STORE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_max_price(user_id: int) -> int:
    with _lock:
        try:
            return int(_load().get(str(user_id), {}).get("max_price", 0))
        except (TypeError, ValueError):
            return 0


def set_max_price(user_id: int, value: int) -> None:
    with _lock:
        data = _load()
        data.setdefault(str(user_id), {})["max_price"] = int(value)
        _save(data)


def log_city_request(user_id: int, city: str) -> None:
    with _lock:
        data = _load()
        entry = data.setdefault(str(user_id), {})
        reqs = entry.setdefault("city_requests", [])
        if city not in reqs:
            reqs.append(city)
        _save(data)


def get_all_city_requests() -> dict[int, list[str]]:
    with _lock:
        data = _load()
        return {
            int(uid): entry.get("city_requests", [])
            for uid, entry in data.items()
            if entry.get("city_requests")
        }