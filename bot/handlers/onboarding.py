import logging

from api_client import backend, ApiError
from keyboards import (
    categories_keyboard,
    main_menu_keyboard,
    CITY_NAMES,
    CATEGORY_NAMES,
    PRICE_LABELS,
)
from user_prefs import get_max_price
from utils import get_user_id, get_temp, set_state, State

log = logging.getLogger(__name__)


async def handle_city(event, payload: str):
    user_id = get_user_id(event)
    city = payload.split(":", 1)[1]

    if city not in CITY_NAMES:
        await _ack(event, "Неизвестный город 🤔")
        return

    tmp = get_temp(user_id)
    tmp["city"] = city
    tmp["categories"] = set()

    await _ack(event)
    await event.message.answer(
        f"🏙 {CITY_NAMES[city]}\n\n"
        f"Что тебе интересно? Отметь несколько вариантов:",
        attachments=[categories_keyboard(tmp["categories"])],
    )


async def handle_no_city(event):
    user_id = get_user_id(event)
    set_state(user_id, State.AWAITING_CITY_NAME)
    await _ack(event)
    await event.message.answer(
        "😔 Очень жаль, что твоего города нет в списке.\n\n"
        "Мы уже работаем над расширением географии. "
        "Напиши название своего города — мы передадим его разработчикам."
    )


async def handle_category(event, payload: str):
    user_id = get_user_id(event)
    action = payload.split(":", 1)[1]
    tmp = get_temp(user_id)

    if "city" not in tmp:
        await _ack(event, "Сначала выбери город 👆")
        return

    selected = tmp.setdefault("categories", set())

    if action == "done":
        if not selected:
            await _ack(event, "Выбери хотя бы одну категорию 👆")
            return
        await _finish_onboarding(event, user_id)
        return

    if action not in CATEGORY_NAMES:
        await _ack(event, "Неизвестная категория 🤔")
        return

    if action in selected:
        selected.discard(action)
    else:
        selected.add(action)

    await _ack(event)

    text = (
        f"🏙 {CITY_NAMES[tmp['city']]}\n\n"
        f"Выбрано: {len(selected)} из {len(CATEGORY_NAMES)}"
    )
    kb = categories_keyboard(selected)

    try:
        await event.edit(text=text, attachments=[kb])
    except Exception:
        log.debug("edit failed, keeping old keyboard")


async def _finish_onboarding(event, user_id: int):
    tmp = get_temp(user_id)
    city = tmp["city"]
    categories = sorted(tmp["categories"])

    try:
        await backend.upsert_user(user_id, city, categories)
    except ApiError as e:
        await _ack(event)
        await event.message.answer(str(e))
        return

    set_state(user_id, State.IDLE)
    tmp.pop("city", None)
    tmp.pop("categories", None)

    max_price = get_max_price(user_id)
    price_label = PRICE_LABELS.get(max_price) or (
        f"до {max_price} ₽" if max_price else "без лимита"
    )

    await _ack(event)
    await event.message.answer(
        f"✅ Профиль готов\n\n"
        f"🏙 {CITY_NAMES[city]}\n"
        f"🏷 {len(categories)} интерес(ов)\n"
        f"💰 {price_label}\n\n"
        f"Что делаем?",
        attachments=[main_menu_keyboard()],
    )


async def _ack(event, text: str | None = None):
    try:
        await event.ack()
    except Exception:
        pass
    if text:
        try:
            await event.message.answer(text)
        except Exception:
            pass