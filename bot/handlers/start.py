from maxapi import Router
from maxapi.filters.command import CommandStart, Command
from maxapi.types import MessageCreated, BotStarted

from api_client import backend, ApiError
from keyboards import (
    city_keyboard,
    main_menu_keyboard,
    back_keyboard,
    PRICE_LABELS,
    CITY_NAMES,
)
from user_prefs import get_max_price
from utils import get_user_id, set_state, State, clear_temp

router = Router()

HELP_TEXT = (
    "❓ Как пользоваться ботом\n\n"
    "🎯 Найти события — подберу по твоим интересам. "
    "Можно искать по всем сразу или по одной категории.\n\n"
    "⏰ Найти под моё время — напиши, когда ты свободен, "
    "например «сб 19:00-23:00», и покажу события в это окно. "
    "Можно несколько окон через запятую.\n\n"
    "💰 Бюджет — задай максимальную сумму события. "
    "Выбери из готовых вариантов или введи свою.\n\n"
    "👤 Профиль и настройки — изменить город и интересы.\n\n"
    "Если что-то сломалось — напиши /reset."
)


def _price_label(user_id: int) -> str:
    max_price = get_max_price(user_id)
    return PRICE_LABELS.get(max_price) or (
        f"до {max_price} ₽" if max_price else "без лимита"
    )


def _city_label(user: dict) -> str:
    key = user.get("city") or ""
    return CITY_NAMES.get(key, key or "—")


@router.bot_started()
async def bot_started_handler(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=(
            "👋 Привет! Я помогу найти события в твоём городе.\n\n"
            "Нажми /start, чтобы начать."
        ),
    )


@router.message_created(CommandStart())
async def start_handler(event: MessageCreated):
    user_id = get_user_id(event)
    clear_temp(user_id)

    try:
        user = await backend.get_user(user_id)
    except ApiError as e:
        await event.message.answer(str(e))
        return

    if user is None or not user.get("city") or not user.get("categories"):
        set_state(user_id, State.ONBOARDING_CITY)
        await event.message.answer(
            "👋 Привет! Давай познакомимся.\n\n"
            "Выбери свой город:",
            attachments=[city_keyboard()],
        )
        return

    set_state(user_id, State.IDLE)
    cats = user.get("categories") or []

    await event.message.answer(
        f"👋 С возвращением!\n\n"
        f"🏙 {_city_label(user)}\n"
        f"🏷 {len(cats)} интерес(ов)\n"
        f"💰 {_price_label(user_id)}\n\n"
        f"Что делаем?",
        attachments=[main_menu_keyboard()],
    )


@router.message_created(Command("help"))
async def help_command(event: MessageCreated):
    await event.message.answer(HELP_TEXT, attachments=[back_keyboard()])


@router.message_created(Command("reset"))
async def reset_command(event: MessageCreated):
    user_id = get_user_id(event)
    clear_temp(user_id)
    set_state(user_id, State.ONBOARDING_CITY)
    await event.message.answer(
        "🔄 Сбрасываю настройки.\n\nВыбери город заново:",
        attachments=[city_keyboard()],
    )