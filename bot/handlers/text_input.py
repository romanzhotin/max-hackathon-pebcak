import logging
import re

from maxapi import Router
from maxapi.types import MessageCreated

from keyboards import city_keyboard, price_keyboard
from time_parser import parse_intervals, format_interval
from user_prefs import log_city_request, set_max_price
from utils import get_user_id, get_state, set_state, State

log = logging.getLogger(__name__)
router = Router()

MIN_PRICE = 50
MAX_PRICE = 100_000

_NUM_RE = re.compile(r"\d+")


@router.message_created()
async def on_text_input(event: MessageCreated):
    user_id = get_user_id(event)
    state = get_state(user_id)

    body = getattr(event.message, "body", None)
    text = (getattr(body, "text", "") or "").strip()

    log.info("text_input: user=%s state=%s text=%r", user_id, state, text[:60])

    if not text or text.startswith("/"):
        return

    if state in (State.AWAITING_PRICE, State.AWAITING_CITY_NAME):
        intervals = parse_intervals(text)
        if intervals:
            await _switch_to_time_search(user_id, event, intervals, state)
            return

    if state == State.AWAITING_CITY_NAME:
        await _handle_city(user_id, event, text)
        return

    if state == State.AWAITING_PRICE:
        await _handle_price(user_id, event, text)
        return

    from handlers import time_search
    handled = await time_search.handle_text(event, text)
    if not handled:
        await event.message.answer(
            "Не понял 🤔\n\n"
            "Выбери действие из меню или напиши интервал вида "
            "«сб 19:00-23:00»."
        )


async def _switch_to_time_search(user_id: int, event, intervals: list, prev_state: State):
    set_state(user_id, State.IDLE)

    labels = [format_interval(iv) for iv in intervals]
    hint = " | ".join(labels)

    if prev_state == State.AWAITING_PRICE:
        preamble = (
            "Похоже, ты хочешь найти события по времени, а не менять лимит.\n"
            "Ок, переключаюсь на поиск 👇"
        )
    elif prev_state == State.AWAITING_CITY_NAME:
        preamble = (
            "Похоже, ты хочешь найти события по времени, а не называть город.\n"
            "Ок, переключаюсь на поиск 👇"
        )
    else:
        preamble = "Ок, ищу по времени 👇"

    await event.message.answer(f"{preamble}\n\n⏰ {hint}")

    from handlers import time_search
    await time_search.run_search(event, user_id, intervals)


async def _handle_city(user_id: int, event, text: str):
    if len(text) > 80:
        await event.message.answer(
            "Название слишком длинное (макс. 80 символов). Попробуй ещё раз."
        )
        return

    log_city_request(user_id, text)
    log.info("city request from %s: %r", user_id, text)

    set_state(user_id, State.ONBOARDING_CITY)
    await event.message.answer(
        f"📝 Спасибо! Записал: «{text}».\n\n"
        f"Передадим запрос разработчикам — работаем над расширением.\n\n"
        f"Пока выбери ближайший крупный город из списка:",
        attachments=[city_keyboard()],
    )


async def _handle_price(user_id: int, event, text: str):
    match = _NUM_RE.search(text)
    if not match:
        await event.message.answer(
            f"Не понял сумму 🤔\n\n"
            f"Напиши число от {MIN_PRICE} до {MAX_PRICE} ₽, например: 700\n\n"
            f"Или, если хочешь поиск по времени, отправь, например:\n"
            f"сб 19:00-23:00"
        )
        return

    value = int(match.group())
    if value < MIN_PRICE:
        await event.message.answer(
            f"Слишком мало. Минимум {MIN_PRICE} ₽. Попробуй ещё раз:"
        )
        return
    if value > MAX_PRICE:
        await event.message.answer(
            f"Слишком много. Максимум {MAX_PRICE} ₽. Попробуй ещё раз:"
        )
        return

    set_max_price(user_id, value)
    set_state(user_id, State.IDLE)

    log.info("custom price set for %s: %d", user_id, value)
    await event.message.answer(
        f"✅ Лимит обновлён: до {value} ₽",
        attachments=[price_keyboard(value)],
    )