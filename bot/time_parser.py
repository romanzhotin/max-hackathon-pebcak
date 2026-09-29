import re
from datetime import datetime

DAYS = {
    "пн": 1, "понедельник": 1,
    "вт": 2, "вторник": 2,
    "ср": 3, "среда": 3,
    "чт": 4, "четверг": 4,
    "пт": 5, "пятница": 5,
    "сб": 6, "суббота": 6,
    "вс": 7, "воскресенье": 7,
}

DAY_RU = {
    1: "пн", 2: "вт", 3: "ср", 4: "чт", 5: "пт", 6: "сб", 7: "вс",
}

_TIME_RE = re.compile(r"(?<!\d)(\d{1,2})[:.\s](\d{2})(?!\d)")
_WORD_RE = re.compile(r"\b([а-яё]+)\b", re.IGNORECASE)
_SPLIT_RE = re.compile(r"[,;|\n]+")


def parse_interval(text: str):
    if not text:
        return None

    text = text.lower().strip()

    times = _TIME_RE.findall(text)
    if len(times) < 2:
        return None

    def _fmt(h, m):
        try:
            hh, mm = int(h), int(m)
        except ValueError:
            return None
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"
        return None

    start = _fmt(*times[0])
    end = _fmt(*times[1])
    if not start or not end:
        return None

    day = None
    for word in _WORD_RE.findall(text):
        if word in DAYS:
            day = DAYS[word]
            break

    return {"day": day, "start": start, "end": end}


def parse_intervals(text: str):
    if not text:
        return []
    parts = _SPLIT_RE.split(text)
    out = []
    for p in parts:
        iv = parse_interval(p.strip())
        if iv:
            out.append(iv)
    return out


def matches(event_dt: datetime, interval: dict) -> bool:
    if interval.get("day") is not None and event_dt.isoweekday() != interval["day"]:
        return False

    h, m = map(int, interval["start"].split(":"))
    start_min = h * 60 + m
    h, m = map(int, interval["end"].split(":"))
    end_min = h * 60 + m

    ev_min = event_dt.hour * 60 + event_dt.minute
    return start_min <= ev_min <= end_min


def format_interval(iv: dict) -> str:
    day = DAY_RU.get(iv["day"], "") if iv.get("day") else ""
    return f"{day} {iv['start']}–{iv['end']}".strip()