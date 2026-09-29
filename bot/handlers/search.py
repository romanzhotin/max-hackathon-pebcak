import asyncio
import logging

from api_client import backend, ApiError
from formatting import format_event, collect_events
from keyboards import (
    CATEGORY_NAMES,
    PRICE_LABELS,
    main_menu_keyboard,
    pagination_keyboard,
    search_filter_keyboard,
)
from user_prefs import get_max_price
from utils import get_user_id, set_state, State

log = logging.getLogger(__name__)

PAGE_SIZE = 5

_searches: dict[int, dict] = {}


async def handle_search(event):
    user_id = get_user_id(event)
    set_state(user_id, State.IDLE)
    await _ack(event)

    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if not user or not user.get("city") or not user.get("categories"):
        await event.message.answer("Профиль не настроен. Нажми /start.")
        return

    cats = user["categories"]
    if len(cats) == 1:
        await _run_search(event, user_id, user, cats)
        return

    max_price = get_max_price(user_id)
    price_label = PRICE_LABELS.get(max_price, f"до {max_price} ₽") if max_price else "без лимита"

    await event.message.answer(
        f"🎯 Что искать?\n💰 Лимит: {price_label}",
        attachments=[search_filter_keyboard(cats)],
    )


async def handle_search_category(event, payload: str):
    user_id = get_user_id(event)
    value = payload.split(":", 1)[1]
    await _ack(event)

    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if not user or not user.get("city") or not user.get("categories"):
        await event.message.answer("Профиль не настроен. Нажми /start.")
        return

    if value == "all":
        cats = user["categories"]
    elif value in CATEGORY_NAMES and value in user["categories"]:
        cats = [value]
    else:
        await event.message.answer("Категория недоступна.")
        return

    await _run_search(event, user_id, user, cats)


async def handle_more(event):
    user_id = get_user_id(event)
    await _ack(event)

    state = _searches.get(user_id)
    if not state:
        await event.message.answer(
            "Предыдущий поиск устарел.",
            attachments=[main_menu_keyboard()],
        )
        return

    await _show_page(event, user_id, state)


async def handle_menu(event):
    user_id = get_user_id(event)
    _searches.pop(user_id, None)
    await _ack(event)
    await event.message.answer("🏠", attachments=[main_menu_keyboard()])


async def _run_search(event, user_id: int, user: dict, categories: list[str]):
    label = "все интересы" if len(categories) > 1 else CATEGORY_NAMES.get(
        categories[0], categories[0]
    )
    max_price = get_max_price(user_id)
    price_hint = f" · до {max_price} ₽" if max_price else ""

    await event.message.answer(f"🔍 Ищу: {label}{price_hint}…")

    sem = asyncio.Semaphore(3)

    async def _fetch(cat: str):
        async with sem:
            try:
                kwargs = {"max_price": max_price} if max_price else {}
                return cat, await backend.get_events(user["city"], cat, **kwargs)
            except ApiError:
                return cat, []

    results = await asyncio.gather(*[_fetch(c) for c in categories])
    events = collect_events(results)

    if not events:
        await event.message.answer(
            "😔 Ничего не нашлось.\n"
            "Попробуй другую категорию, поднять лимит или зайти позже.",
            attachments=[main_menu_keyboard()],
        )
        return

    _searches[user_id] = {"events": events, "shown": 0}
    await event.message.answer(f"Нашёл {len(events)} событий:")
    await _show_page(event, user_id, _searches[user_id])


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
        attachments=[pagination_keyboard("s", shown, total)],
    )


async def _ack(event):
    try:
        await event.ack()
    except Exception:
        pass