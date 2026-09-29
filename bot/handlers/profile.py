import logging

from api_client import backend, ApiError
from keyboards import (
    city_keyboard,
    categories_keyboard,
    profile_keyboard,
    price_keyboard,
    PRICE_LABELS,
    CITY_NAMES,
    CATEGORY_NAMES,
)
from user_prefs import get_max_price, set_max_price
from utils import get_user_id, set_state, State, get_temp

log = logging.getLogger(__name__)


def _city_label(user: dict) -> str:
    key = user.get("city") or ""
    return CITY_NAMES.get(key, key or "—")


def _price_label(user_id: int) -> str:
    max_price = get_max_price(user_id)
    return PRICE_LABELS.get(max_price) or (
        f"до {max_price} ₽" if max_price else "без лимита"
    )


async def handle_profile(event):
    user_id = get_user_id(event)
    set_state(user_id, State.IDLE)
    await _ack(event)

    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if not user:
        await event.message.answer("Профиль не найден. Нажми /start.")
        return

    cats = user.get("categories") or []
    cat_names = ", ".join(CATEGORY_NAMES.get(c, c) for c in cats) or "—"

    text = (
        f"👤 Твой профиль\n\n"
        f"🏙 {_city_label(user)}\n"
        f"🏷 {cat_names}\n"
        f"💰 {_price_label(user_id)}"
    )
    await event.message.answer(text, attachments=[profile_keyboard()])


async def handle_budget(event):
    user_id = get_user_id(event)
    set_state(user_id, State.IDLE)
    await _ack(event)
    current = get_max_price(user_id)
    await event.message.answer(
        "💰 До какой суммы искать события?",
        attachments=[price_keyboard(current)],
    )


async def handle_price(event, payload: str):
    user_id = get_user_id(event)
    value = payload.split(":", 1)[1]

    if value == "custom":
        set_state(user_id, State.AWAITING_PRICE)
        await _ack(event)
        await event.message.answer(
            "✏️ Напиши свою максимальную сумму в рублях.\n"
            "Например: 700"
        )
        return

    try:
        price = int(value)
    except ValueError:
        await _ack(event)
        return

    set_max_price(user_id, price)
    set_state(user_id, State.IDLE)
    await _ack(event)

    label = PRICE_LABELS.get(price) or (f"до {price} ₽" if price else "без лимита")
    await event.message.answer(
        f"✅ Лимит обновлён: {label}",
        attachments=[price_keyboard(price)],
    )


async def handle_edit_city(event):
    user_id = get_user_id(event)
    tmp = get_temp(user_id)
    tmp["city"] = None
    tmp["categories"] = set()
    set_state(user_id, State.ONBOARDING_CITY)
    await _ack(event)
    await event.message.answer(
        "🏙 Выбери новый город:",
        attachments=[city_keyboard()],
    )


async def handle_edit_cats(event):
    user_id = get_user_id(event)
    tmp = get_temp(user_id)
    await _ack(event)

    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if not user or not user.get("city"):
        await event.message.answer("Сначала выбери город: /start")
        return

    tmp["city"] = user["city"]
    tmp["categories"] = set(user.get("categories") or [])
    set_state(user_id, State.ONBOARDING_CATEGORIES)

    await event.message.answer(
        "🏷 Отметь нужные категории и нажми «Готово»:",
        attachments=[categories_keyboard(tmp["categories"])],
    )


async def _ack(event):
    try:
        await event.ack()
    except Exception:
        pass