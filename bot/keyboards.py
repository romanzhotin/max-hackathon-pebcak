from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

CITIES = [
    ("msk", "Москва"),
    ("spb", "СПб"),
    ("nn", "Нижний Новгород"),
    ("kzn", "Казань"),
    ("hbr", "Хабаровск"),
]

CATEGORIES = [
    ("koncert", "🎵 Концерты"),
    ("teatr", "🎭 Театр"),
    ("shou", "✨ Шоу"),
    ("kino", "🎬 Кино"),
    ("children", "🧸 Детям"),
    ("festivals", "🎉 Фестивали"),
    ("excursions", "🚶 Экскурсии"),
    ("sport", "⚽ Спорт"),
    ("education", "📚 Образование"),
]

CITY_NAMES = dict(CITIES)
CATEGORY_NAMES = dict(CATEGORIES)

PRICE_OPTIONS = [
    (0, "🚫 Без лимита"),
    (300, "до 300 ₽"),
    (500, "до 500 ₽"),
    (1000, "до 1000 ₽"),
    (2000, "до 2000 ₽"),
]
PRICE_LABELS = {v: label for v, label in PRICE_OPTIONS}


def _build(rows):
    builder = InlineKeyboardBuilder()
    for row in rows:
        builder.row(*[CallbackButton(text=t, payload=p) for t, p in row])
    return builder.as_markup()


def city_keyboard():
    rows = []
    for i in range(0, len(CITIES), 2):
        rows.append([(name, f"city:{code}") for code, name in CITIES[i:i + 2]])
    rows.append([("❌ Нет моего города", "city:none")])
    return _build(rows)


def categories_keyboard(selected: set[str]):
    pairs = []
    for code, name in CATEGORIES:
        mark = "✅ " if code in selected else ""
        pairs.append((f"{mark}{name}", f"cat:{code}"))
    rows = [pairs[i:i + 2] for i in range(0, len(pairs), 2)]
    rows.append([(f"➡️ Готово ({len(selected)})", "cat:done")])
    return _build(rows)


def main_menu_keyboard():
    return _build([
        [("🎯 Найти события", "menu:search")],
        [("⏰ Найти под моё время", "menu:search_time")],
        [("💰 Бюджет", "menu:budget")],
        [("👤 Профиль и настройки", "menu:profile")],
        [("❓ Помощь", "menu:help")],
    ])


def profile_keyboard():
    return _build([
        [("⚙️ Изменить интересы", "menu:edit_cats")],
        [("💰 Бюджет", "menu:budget")],
        [("🏙 Сменить город", "menu:edit_city")],
        [("🏠 В меню", "menu:back")],
    ])


def price_keyboard(current: int = 0):
    rows = []
    pairs = []
    for value, label in PRICE_OPTIONS:
        mark = "✅ " if value == current else ""
        pairs.append((f"{mark}{label}", f"price:{value}"))
    for i in range(0, len(pairs), 2):
        rows.append(pairs[i:i + 2])

    is_custom = current > 0 and current not in PRICE_LABELS
    if is_custom:
        rows.insert(0, [(f"✅ до {current} ₽", f"price:{current}")])

    rows.append([("✏️ Своя сумма", "price:custom")])
    rows.append([("🏠 В меню", "menu:back")])
    return _build(rows)


def search_filter_keyboard(user_categories: list[str]):
    rows = [[("🎯 Все интересы", "search_cat:all")]]
    pairs = [
        (CATEGORY_NAMES[c], f"search_cat:{c}")
        for c in user_categories
        if c in CATEGORY_NAMES
    ]
    for i in range(0, len(pairs), 2):
        rows.append(pairs[i:i + 2])
    rows.append([("🏠 В меню", "menu:back")])
    return _build(rows)


def pagination_keyboard(prefix: str, shown: int, total: int):
    rows = []
    if shown < total:
        remaining = total - shown
        rows.append([(f"⬇️ Ещё {remaining}", f"{prefix}:more")])
    rows.append([("🏠 В меню", f"{prefix}:menu")])
    return _build(rows)


def back_keyboard(payload: str = "menu:back", text: str = "🏠 В меню"):
    return _build([[(text, payload)]])