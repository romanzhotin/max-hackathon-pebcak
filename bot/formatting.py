from datetime import datetime, timezone, timedelta

from keyboards import CATEGORY_NAMES

MSK = timezone(timedelta(hours=3))
WEEKDAYS_RU = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def dedupe_key(ev: dict) -> str:
    url = ev.get("url") or (ev.get("offers") or {}).get("url")
    if url:
        return f"url::{url}"
    name = (ev.get("name") or "").strip().lower()
    dt = ev.get("startDate") or ""
    return f"nd::{name}::{dt}"


def format_event(ev: dict) -> str:
    name = ev.get("name", "Без названия")
    lines = [f"🎭 {name}"]

    dt = ev.get("_dt") or parse_dt(ev.get("startDate"))
    if dt is not None:
        local = dt.astimezone(MSK)
        wd = WEEKDAYS_RU[local.weekday()]
        lines.append(f"📅 {wd}, {local.strftime('%d.%m в %H:%M')}")

    loc = ev.get("location") or {}
    if isinstance(loc, dict):
        loc_name = loc.get("name") or ((loc.get("address") or {}).get("addressLocality"))
        if loc_name:
            lines.append(f"📍 {loc_name}")

    offers = ev.get("offers") or {}
    if isinstance(offers, dict):
        price = offers.get("price")
        if price is not None:
            lines.append(f"💰 {price} ₽")

    cats = ev.get("_categories") or []
    cat_labels = [CATEGORY_NAMES[c] for c in cats if c in CATEGORY_NAMES]
    if cat_labels:
        lines.append(f"🏷 {', '.join(cat_labels)}")

    url = (ev.get("offers") or {}).get("url") or ev.get("url")
    if url:
        lines.append(f"🔗 {url}")

    return "\n".join(lines)


def collect_events(results, predicate=None):
    by_key: dict[str, dict] = {}

    for cat, events in results:
        for ev in events:
            dt = parse_dt(ev.get("startDate"))
            if dt is None:
                continue
            if predicate is not None and not predicate(ev, dt):
                continue

            dt_msk = dt.astimezone(MSK)
            key = dedupe_key(ev)
            existing = by_key.get(key)
            if existing is not None:
                if cat not in existing["_categories"]:
                    existing["_categories"].append(cat)
            else:
                ev["_dt"] = dt_msk
                ev["_categories"] = [cat]
                by_key[key] = ev

    return sorted(by_key.values(), key=lambda e: e["_dt"])