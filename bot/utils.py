from enum import Enum


def get_user_id(event) -> int:
    from_user = getattr(event, "from_user", None)
    if from_user is not None:
        for attr in ("id", "user_id"):
            uid = getattr(from_user, attr, None)
            if uid is not None:
                return int(uid)

    user = getattr(event, "user", None)
    if user is not None:
        uid = getattr(user, "id", None)
        if uid is not None:
            return int(uid)

    msg = getattr(event, "message", None)
    if msg is not None:
        sender = getattr(msg, "sender", None)
        if sender is not None:
            for attr in ("id", "user_id"):
                uid = getattr(sender, attr, None)
                if uid is not None:
                    return int(uid)

    for attr in ("user_id", "chat_id"):
        uid = getattr(event, attr, None)
        if uid is not None:
            return int(uid)

    raise RuntimeError(f"Не могу достать user_id из {type(event).__name__}")


def get_chat_id(event) -> int:
    cid = getattr(event, "chat_id", None)
    if cid is not None:
        return int(cid)

    chat = getattr(event, "chat", None)
    if chat is not None:
        cid = getattr(chat, "id", None)
        if cid is not None:
            return int(cid)

    msg = getattr(event, "message", None)
    if msg is not None:
        cid = getattr(msg, "chat_id", None)
        if cid is not None:
            return int(cid)

    raise RuntimeError("Не могу достать chat_id")


class State(str, Enum):
    IDLE = "idle"
    ONBOARDING_CITY = "onboarding_city"
    ONBOARDING_CATEGORIES = "onboarding_categories"
    AWAITING_CITY_NAME = "awaiting_city_name"
    AWAITING_PRICE = "awaiting_price"


_states: dict[int, State] = {}
_temp: dict[int, dict] = {}


def get_state(user_id: int) -> State:
    return _states.get(user_id, State.IDLE)


def set_state(user_id: int, state: State) -> None:
    _states[user_id] = state


def get_temp(user_id: int) -> dict:
    return _temp.setdefault(user_id, {})


def clear_temp(user_id: int) -> None:
    _temp.pop(user_id, None)