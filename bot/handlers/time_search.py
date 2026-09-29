import asyncio
import logging

from api_client import backend, ApiError
from formatting import format_event, collect_events
from keyboards import (
    main_menu_keyboard,
    pagination_keyboard,
)
from time_parser import parse_intervals, matches, format_interval
from user_prefs import get_max_price
from utils import get_user_id, set_state, State

log = logging.getLogger(__name__)

PAGE_SIZE = 5

PROMPT_TEXT = (
    "⏰ Когда ты свободен?\n\n"
    "Напиши так:\n"
    "• сб 19:00-23:00\n"
    "• пт 18:30-22:00\n"
    "• 19:00-23:00 (любой день)\n\n"
    "Можно несколько окон через запятую:\n"
    "• сб 19:00-23:00, вс 10:00-14:00"
)

_searches: dict[int, dict] = {}


async def handle_text(event, text: str) -> bool:
    if len(text) > 200:
        return False

    intervals = parse_intervals(text)
    if not intervals:
        log.debug("handle_text: not an interval, skip")
        return False

    user_id = get_user_id(event)
    await run_search(event, user_id, intervals)
    return True


async def run_search(event, user_id: int, intervals: list[dict]):
    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if not user or not user.get("city") or not user.get("categories"):
        await event.message.answer("Профиль не настроен. Нажми /start.")
        return

    labels = [format_interval(iv) for iv in intervals]
    label = " | ".join(labels)
    max_price = get_max_price(user_id)
    price_hint = f" · до {max_price} ₽" if max_price else ""

    await event.message.answer(f"🔍 Ищу на {label}{price_hint}…")

    sem = asyncio.Semaphore(3)

    async def _fetch(cat: str):
        async with sem:
            try:
                kwargs = {"max_price": max_price} if max_price else {}
                return cat, await backend.get_events(user["city"], cat, **kwargs)
            except ApiError:
                return cat, []

    results = await asyncio.gather(*[_fetch(c) for c in user["categories"]])

    def _predicate(_ev, dt):
        return any(matches(dt, iv) for iv in intervals)

    events = collect_events(results, predicate=_predicate)

    if not events:
        await event.message.answer(
            "😔 На эти окна ничего не нашлось.\n"
            "Попробуй расширить время, поднять лимит или другой день.",
            attachments=[main_menu_keyboard()],
        )
        return

    _searches[user_id] = {
        "events": events,
        "shown": 0,
        "intervals": intervals,
    }

    await event.message.answer(f"Нашёл {len(events)} событий под твои окна:")
    await _show_page(event, user_id, _searches[user_id])


async def handle_button(event):
    user_id = get_user_id(event)
    set_state(user_id, State.IDLE)
    await _ack(event)
    await event.message.answer(PROMPT_TEXT)


async def handle_more(event):
    user_id = get_user_id(event)
    await _ack(event)

    state = _searches.get(user_id)
    if not state:
        await event.message.answer(
            "Поиск устарел. Задай интервал заново.",
            attachments=[main_menu_keyboard()],
        )
        return

    await _show_page(event, user_id, state)


async def handle_menu(event):
    user_id = get_user_id(event)
    _searches.pop(user_id, None)
    await _ack(event)
    await event.message.answer("🏠", attachments=[main_menu_keyboard()])


async def _show_page(event, user_id: int, state: dict):
    events = state["events"]
    start = state["shown"]
    end = min(start + PAGE_SIZE, len(events))

    for ev in events[start:end]:
        await event.message.answer(format_event(ev))

    state["shown"] = end
    total = len(events)
    shown = state["shown"]

    footer = (
        f"Показано {shown} из {total}."
        if shown < total
        else f"Это все {total} событий."
    )
    await event.message.answer(
        footer,
        attachments=[pagination_keyboard("ts", shown, total)],
    )


async def _ack(event):
    try:
        await event.ack()
    except Exception:
        pass