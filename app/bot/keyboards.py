"""Все inline-клавиатуры бота в одном месте."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.common import short


def back_to(menu_data: str = "menu", text: str = "⬅️ Назад") -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.button(text=text, callback_data=menu_data)
    return b


# ---------------------------------------------------------------- main
def main_menu(counts: dict) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    leads = counts.get("new_leads", 0)
    b.button(text="👤 Профиль и контакты", callback_data="pf")
    b.button(text=f"🗂 Разделы работ ({counts.get('categories', 0)})", callback_data="cat")
    b.button(text=f"📸 Фотосеты ({counts.get('albums', 0)})", callback_data="alb")
    b.button(text=f"🖼 Избранное ({counts.get('standalone', 0)})", callback_data="sel")
    b.button(text=f"💼 Услуги ({counts.get('services', 0)})", callback_data="svc")
    b.button(text=f"🏆 Выставки ({counts.get('exhibitions', 0)})", callback_data="ex")
    b.button(text=f"💬 Заявки ({leads})" + (" 🔴" if leads else ""), callback_data="leads")
    b.button(text="👥 Администраторы", callback_data="admins")
    b.button(text="📊 Статистика", callback_data="stats")
    b.button(text="💾 Бэкап", callback_data="backup")
    b.button(text="📷 Открыть приложение", callback_data="openapp")
    b.adjust(1)
    return b.as_markup()


# ---------------------------------------------------------------- profile
PROFILE_FIELDS: list[tuple[str, str, str]] = [
    ("brand_name", "✨ Имя / бренд", "Как подписано портфолио — в шапке, на главном экране и в стартовой надписи при загрузке. По умолчанию: kolpako_v"),
    ("tagline", "💫 Слоган", "Короткая строка под именем"),
    ("about", "📝 О себе", "Пара абзацев. Можно с переносами строк"),
    ("facts", "📌 Факты", "Каждый факт с новой строки"),
    ("city", "📍 Город", "Например: Москва · работаю по всему миру"),
    ("phone", "📞 Телефон", "Например: +7 (900) 123-45-67"),
    ("telegram", "✈️ Telegram", "Ссылка, например: https://t.me/username"),
    ("whatsapp", "🟢 WhatsApp", "Номер цифрами, например: 79001234567"),
    ("instagram", "📸 Instagram", "Ссылка на профиль"),
    ("behance", "🎨 Behance", "Ссылка на профиль"),
    ("email", "✉️ Email", "Почта для связи"),
    ("experience_years", "🎓 Лет опыта", "Число, например: 12"),
    ("shoots_count", "📷 Съёмок", "Например: 900+"),
    ("countries_count", "🌍 Стран", "Например: 30"),
    ("currency", "💱 Валюта", "Символ: ₽, $, €..."),
    ("webapp_url", "🔗 Адрес веб-приложения", "Публичный https-адрес приложения"),
]

PROFILE_LABELS = {k: v for k, v, _ in PROFILE_FIELDS}


def profile_menu(settings: dict) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label, _ in PROFILE_FIELDS:
        val = short(settings.get(key, ""), 22)
        b.button(text=f"{label}: {val or '—'}", callback_data=f"pf:set:{key}")
    b.button(text="🖼 Аватарка", callback_data="pf:avatar")
    b.button(text="🌄 Фото для главного экрана", callback_data="pf:hero")
    booking = settings.get("booking_enabled", "1") == "1"
    b.button(text=f"{'🟢' if booking else '🔴'} Запись: {'вкл' if booking else 'выкл'}", callback_data="pf:toggle:booking")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


# ---------------------------------------------------------------- categories
def categories_list(cats: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"📁 {c['title']} ({c.get('albums_count', 0)})", callback_data=f"cat:view:{c['id']}")
    b.button(text="➕ Новый раздел", callback_data="cat:add")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def category_card(cat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Название", callback_data=f"cat:ren:{cat_id}")
    b.button(text="📝 Подзаголовок", callback_data=f"cat:sub:{cat_id}")
    b.button(text="📸 Фотосеты раздела", callback_data=f"alb:cat:{cat_id}")
    b.button(text="⬆️ Выше", callback_data=f"cat:up:{cat_id}")
    b.button(text="⬇️ Ниже", callback_data=f"cat:dn:{cat_id}")
    b.button(text="🗑 Удалить", callback_data=f"cat:del:{cat_id}")
    b.button(text="⬅️ К разделам", callback_data="cat")
    b.adjust(2, 1, 2, 1, 1)
    return b.as_markup()


# ---------------------------------------------------------------- albums
def album_categories(cats: list[dict], action: str = "alb:cat") -> InlineKeyboardMarkup:
    """Выбор раздела: action — префикс колбэка + :{id}."""
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"📁 {c['title']}", callback_data=f"{action}:{c['id']}")
    b.button(text="⬅️ Назад", callback_data="alb")
    b.adjust(1)
    return b.as_markup()


def albums_list(albums: list[dict], cat_id: int, counts: dict[int, int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for a in albums:
        eye = "" if a["is_visible"] else "🙈 "
        b.button(text=f"{eye}📸 {a['title']} ({counts.get(a['id'], 0)})", callback_data=f"alb:view:{a['id']}")
    b.button(text="➕ Новый фотосет", callback_data=f"alb:add:{cat_id}")
    b.button(text="⬅️ К разделам", callback_data="alb")
    b.adjust(1)
    return b.as_markup()


def album_card(album: dict, photos_count: int) -> InlineKeyboardMarkup:
    aid = album["id"]
    b = InlineKeyboardBuilder()
    b.button(text=f"🖼 Фотографии ({photos_count})", callback_data=f"alb:ph:{aid}")
    b.button(text="📥 Загрузить фото", callback_data=f"alb:up:{aid}")
    b.button(text="✏️ Название", callback_data=f"alb:edit:{aid}:title")
    b.button(text="📝 Описание", callback_data=f"alb:edit:{aid}:description")
    b.button(text="📍 Локация", callback_data=f"alb:edit:{aid}:location")
    b.button(text="📅 Год", callback_data=f"alb:edit:{aid}:year")
    b.button(text="📁 Сменить раздел", callback_data=f"alb:movecat:{aid}")
    eye = "🙈 Скрыть" if album["is_visible"] else "👁 Показать"
    b.button(text=eye, callback_data=f"alb:vis:{aid}")
    b.button(text="⬆️ Выше", callback_data=f"alb:uppos:{aid}")
    b.button(text="⬇️ Ниже", callback_data=f"alb:dnpos:{aid}")
    b.button(text="🗑 Удалить фотосет", callback_data=f"alb:del:{aid}")
    b.button(text="⬅️ К фотосетам", callback_data=f"alb:cat:{album['category_id']}")
    b.adjust(1, 1, 2, 2, 1, 1, 2, 1, 1)
    return b.as_markup()


ALBUM_FIELD_LABELS = {"title": "название", "description": "описание", "location": "локацию", "year": "год"}


def photos_list(photos: list[dict], ctx: str, back_data: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, p in enumerate(photos, 1):
        cap = short(p["caption"], 24)
        b.button(text=f"{i}. {cap or 'без подписи'}", callback_data=f"ph:view:{p['id']}:{ctx}")
    b.button(text="⬅️ Назад", callback_data=back_data)
    b.adjust(1)
    return b.as_markup()


def photo_card(photo_id: int, ctx: str, back_data: str, is_cover: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Подпись", callback_data=f"ph:cap:{photo_id}:{ctx}")
    if ctx.startswith("a") or ctx.startswith("s"):
        star = "⭐ Это обложка" if is_cover else "⭐ Сделать обложкой"
        b.button(text=star, callback_data=f"ph:cov:{photo_id}:{ctx}")
    b.button(text="⬆️ Выше", callback_data=f"ph:up:{photo_id}:{ctx}")
    b.button(text="⬇️ Ниже", callback_data=f"ph:dn:{photo_id}:{ctx}")
    b.button(text="🗑 Удалить", callback_data=f"ph:del:{photo_id}:{ctx}")
    b.button(text="⬅️ Назад", callback_data=back_data)
    b.adjust(1, 2, 1, 1)
    return b.as_markup()


# ---------------------------------------------------------------- services
def services_list(services: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in services:
        dot = "🟢" if s["is_active"] else "🔴"
        price = f" — {s['price']}" if s["price"] else ""
        b.button(text=f"{dot} {s['title']}{price}", callback_data=f"svc:view:{s['id']}")
    b.button(text="➕ Новая услуга", callback_data="svc:add")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def service_card(svc: dict, photos_count: int) -> InlineKeyboardMarkup:
    sid = svc["id"]
    b = InlineKeyboardBuilder()
    b.button(text="🖼 Обложка" + (" ✅" if svc["cover_path"] else ""), callback_data=f"svc:cover:{sid}")
    b.button(text=f"📷 Фото услуги ({photos_count})", callback_data=f"svc:ph:{sid}")
    b.button(text="📥 Прикрепить фото", callback_data=f"svc:up:{sid}")
    b.button(text="✏️ Название", callback_data=f"svc:edit:{sid}:title")
    b.button(text="📝 Описание", callback_data=f"svc:edit:{sid}:description")
    b.button(text="💰 Цена", callback_data=f"svc:edit:{sid}:price")
    b.button(text="🏷 Уточнение цены", callback_data=f"svc:edit:{sid}:price_note")
    b.button(text="⏱ Длительность", callback_data=f"svc:edit:{sid}:duration")
    tog = "🔴 Выключить" if svc["is_active"] else "🟢 Включить"
    b.button(text=tog, callback_data=f"svc:toggle:{sid}")
    b.button(text="⬆️ Выше", callback_data=f"svc:uppos:{sid}")
    b.button(text="⬇️ Ниже", callback_data=f"svc:dnpos:{sid}")
    b.button(text="🗑 Удалить", callback_data=f"svc:del:{sid}")
    b.button(text="⬅️ К услугам", callback_data="svc")
    b.adjust(1, 1, 1, 2, 2, 1, 2, 1, 1)
    return b.as_markup()


SVC_FIELD_LABELS = {
    "title": "название", "description": "описание", "price": "цену",
    "price_note": "уточнение цены", "duration": "длительность",
}


# ---------------------------------------------------------------- exhibitions
def exhibitions_list(items: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for e in items:
        meta = " ".join(x for x in (e["year"], e["place"]) if x)
        b.button(text=f"🏆 {e['title']}" + (f" ({meta})" if meta else ""), callback_data=f"ex:view:{e['id']}")
    b.button(text="➕ Добавить", callback_data="ex:add")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def exhibition_card(ex_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Название", callback_data=f"ex:edit:{ex_id}:title")
    b.button(text="📍 Место", callback_data=f"ex:edit:{ex_id}:place")
    b.button(text="📅 Год", callback_data=f"ex:edit:{ex_id}:year")
    b.button(text="📝 Описание", callback_data=f"ex:edit:{ex_id}:description")
    b.button(text="⬆️ Выше", callback_data=f"ex:up:{ex_id}")
    b.button(text="⬇️ Ниже", callback_data=f"ex:dn:{ex_id}")
    b.button(text="🗑 Удалить", callback_data=f"ex:del:{ex_id}")
    b.button(text="⬅️ К выставкам", callback_data="ex")
    b.adjust(2, 2, 2, 1, 1)
    return b.as_markup()


EX_FIELD_LABELS = {"title": "название", "place": "место", "year": "год", "description": "описание"}


# ---------------------------------------------------------------- leads
LEAD_STATUS = {"new": "🆕 Новая", "accepted": "✅ Принята", "declined": "❌ Отклонена"}


def leads_list(leads: list[dict], show_all: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for lead in leads:
        st = LEAD_STATUS.get(lead["status"], lead["status"])
        b.button(text=f"{st} · {short(lead['name'], 16)} — {short(lead['service_title'] or 'без услуги', 16)}",
                 callback_data=f"lead:view:{lead['id']}")
    if show_all:
        b.button(text="🆕 Только новые", callback_data="leads")
    else:
        b.button(text="📋 Все заявки", callback_data="leads:all")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def lead_card(lead_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Принять", callback_data=f"lead:ok:{lead_id}")
    b.button(text="❌ Отклонить", callback_data=f"lead:no:{lead_id}")
    b.button(text="🆕 Вернуть в новые", callback_data=f"lead:new:{lead_id}")
    b.button(text="⬅️ К заявкам", callback_data="leads")
    b.adjust(2, 1, 1)
    return b.as_markup()


# ---------------------------------------------------------------- admins / misc
def admins_list(admins: list[int], env_ids: list[int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for uid in admins:
        lock = " 🔒" if uid in env_ids else ""
        b.button(text=f"👤 {uid}{lock}", callback_data=f"adm:noop:{uid}")
    for uid in admins:
        if uid not in env_ids:
            b.button(text=f"➖ Убрать {uid}", callback_data=f"adm:del:{uid}")
    b.button(text="➕ Добавить админа", callback_data="adm:add")
    b.button(text="ℹ️ Как узнать ID", callback_data="adm:help")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def confirm_kb(yes_data: str, no_data: str, yes_text: str = "✅ Да, удалить") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=yes_text, callback_data=yes_data)
    b.button(text="⬅️ Отмена", callback_data=no_data)
    b.adjust(1)
    return b.as_markup()


def skip_kb(skip_data: str = "add:skip") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⏭ Пропустить", callback_data=skip_data)
    b.button(text="❌ Отмена", callback_data="add:cancel")
    b.adjust(2)
    return b.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data="add:cancel")
    return b.as_markup()


def done_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )
