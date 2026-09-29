import logging

from maxapi import Router
from maxapi.types import MessageCallback

log = logging.getLogger(__name__)
router = Router()


@router.message_callback()
async def on_callback(event: MessageCallback):
    payload = getattr(event.callback, "payload", None) or ""
    log.info("callback payload=%r", payload)

    from handlers import onboarding, profile, search, time_search

    try:
        if payload == "city:none":
            await onboarding.handle_no_city(event)
        elif payload.startswith("city:"):
            await onboarding.handle_city(event, payload)
        elif payload.startswith("cat:"):
            await onboarding.handle_category(event, payload)

        elif payload == "menu:search":
            await search.handle_search(event)
        elif payload.startswith("search_cat:"):
            await search.handle_search_category(event, payload)
        elif payload == "menu:search_time":
            await time_search.handle_button(event)
        elif payload == "menu:profile":
            await profile.handle_profile(event)
        elif payload == "menu:budget":
            await profile.handle_budget(event)
        elif payload.startswith("price:"):
            await profile.handle_price(event, payload)
        elif payload == "menu:help":
            await _show_help(event)
        elif payload == "menu:back":
            await _show_main_menu(event)

        elif payload == "s:more":
            await search.handle_more(event)
        elif payload == "s:menu":
            await search.handle_menu(event)
        elif payload == "ts:more":
            await time_search.handle_more(event)
        elif payload == "ts:menu":
            await time_search.handle_menu(event)

        elif payload == "menu:edit_city":
            await profile.handle_edit_city(event)
        elif payload == "menu:edit_cats":
            await profile.handle_edit_cats(event)

        else:
            log.warning("unknown callback payload=%r", payload)
            try:
                await event.ack()
            except Exception:
                pass
    except Exception:
        log.exception("callback handler failed, payload=%r", payload)


async def _show_help(event):
    from handlers.start import HELP_TEXT
    from keyboards import back_keyboard
    try:
        await event.ack()
    except Exception:
        pass
    await event.message.answer(HELP_TEXT, attachments=[back_keyboard()])


async def _show_main_menu(event):
    from api_client import backend, ApiError
    from keyboards import main_menu_keyboard, PRICE_LABELS, CITY_NAMES
    from user_prefs import get_max_price
    from utils import get_user_id, set_state, State

    try:
        await event.ack()
    except Exception:
        pass

    user_id = get_user_id(event)
    set_state(user_id, State.IDLE)

    try:
        user = await backend.get_user(user_id)
    except ApiError:
        user = None

    max_price = get_max_price(user_id)
    price_label = PRICE_LABELS.get(max_price) or (
        f"до {max_price} ₽" if max_price else "без лимита"
    )

    if user and user.get("city"):
        key = user["city"]
        city = CITY_NAMES.get(key, key or "—")
        cats = user.get("categories") or []
        text = (
            f"🏠 Главное меню\n\n"
            f"🏙 {city}\n"
            f"🏷 {len(cats)} интерес(ов)\n"
            f"💰 {price_label}"
        )
    else:
        text = f"🏠 Главное меню\n\n💰 {price_label}"

    await event.message.answer(text, attachments=[main_menu_keyboard()])