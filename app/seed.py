"""Первичное наполнение сайта демо-контентом.

Запускается один раз при первом старте (флаг settings.seeded).
Всё наполнение потом меняется через бота: тексты, цены, фото.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app import db
from app.config import get_settings
from app.images import process_image_bytes

log = logging.getLogger(__name__)

SEED_DIR = Path(__file__).parent / "seed_assets"

DEFAULT_SETTINGS = {
    "brand_name": "SANEK",
    "tagline": "Fine-art & editorial photographer",
    "about": (
        "Фотограф мирового класса. Работаю на стыке fashion-editorial и fine art: "
        "съёмки для журналов и брендов, частные сессии и выставочные серии.\n\n"
        "Участник международных выставок и фотофестивалей. Мои работы находятся "
        "в частных коллекциях в Европе, США и Азии."
    ),
    "facts": "12 лет за камерой\n900+ проведённых съёмок\n30 стран\nПубликации в Vogue, GQ, Harper's Bazaar",
    "city": "Москва · работаю по всему миру",
    "phone": "+7 (900) 000-00-00",
    "telegram": "https://t.me/username",
    "whatsapp": "79000000000",
    "instagram": "https://instagram.com/username",
    "behance": "https://behance.net/username",
    "email": "hello@example.com",
    "experience_years": "12",
    "shoots_count": "900+",
    "countries_count": "30",
    "currency": "₽",
    "booking_enabled": "1",
}


async def _seed_image(name: str) -> dict | None:
    """Копирует bundled-сид в uploads через общий пайплайн обработки."""
    src = SEED_DIR / name
    if not src.exists():
        log.warning("seed asset missing: %s", name)
        return None
    data = src.read_bytes()
    try:
        return process_image_bytes(data, get_settings().upload_dir)
    except Exception:
        log.exception("seed image failed: %s", name)
        return None


async def seed_if_empty() -> None:
    if await db.get_setting("seeded"):
        return
    log.info("seeding demo content...")

    for key, value in DEFAULT_SETTINGS.items():
        if not await db.get_setting(key):
            await db.set_setting(key, value)

    hero = await _seed_image("seed_hero.jpg")
    if hero:
        await db.set_setting("hero_path", hero["file"])
        await db.set_setting("hero_thumb", hero["thumb"])
    avatar = await _seed_image("seed_avatar.jpg")
    if avatar:
        await db.set_setting("avatar_path", avatar["file"])
        await db.set_setting("avatar_thumb", avatar["thumb"])

    # --- разделы и фотосеты ---
    editorial = await db.add_category("Editorial", "Журналы, бренды, кампании")
    fineart = await db.add_category("Fine Art", "Выставочные серии")
    wedding = await db.add_category("Wedding", "Свадебные истории")

    alb1 = await db.add_album(
        editorial, "Northern Light",
        "Editorial для Vogue Scandinavia. Холодный свет, северный ветер и тишина.",
        "Стокгольм", "2025",
    )
    for name in ("seed_ed1.jpg", "seed_ed2.jpg", "seed_ed3.jpg"):
        pic = await _seed_image(name)
        if pic:
            await db.add_photo(pic["file"], pic["thumb"], width=pic["w"], height=pic["h"], album_id=alb1)

    alb2 = await db.add_album(
        editorial, "Muse — Studio Series",
        "Студийная серия о форме и свете.", "Париж", "2024",
    )
    for name in ("seed_ed4.jpg", "seed_ed5.jpg"):
        pic = await _seed_image(name)
        if pic:
            await db.add_photo(pic["file"], pic["thumb"], width=pic["w"], height=pic["h"], album_id=alb2)

    alb3 = await db.add_album(
        fineart, "Silence",
        "Выставочная серия. Параллельная программа Венецианской биеннале.",
        "Венеция", "2025",
    )
    for name in ("seed_fa1.jpg", "seed_fa2.jpg"):
        pic = await _seed_image(name)
        if pic:
            await db.add_photo(pic["file"], pic["thumb"], width=pic["w"], height=pic["h"], album_id=alb3)

    alb4 = await db.add_album(
        wedding, "Amalfi — Elopement",
        "Камерная свадьба на побережье Амальфи.", "Амальфи", "2024",
    )
    pic = await _seed_image("seed_wed1.jpg")
    if pic:
        await db.add_photo(pic["file"], pic["thumb"], width=pic["w"], height=pic["h"], album_id=alb4)

    # избранное (standalone)
    pic = await _seed_image("seed_sel1.jpg")
    if pic:
        await db.add_photo(pic["file"], pic["thumb"], caption="Selected work", width=pic["w"], height=pic["h"])

    # --- услуги ---
    s1 = await db.add_service(
        "Портретная съёмка",
        "Индивидуальная сессия: образ, свет, локация. Подходит для личного бренда, модельного портфолио и просто для себя.\n• до 3 часов съёмки\n• 30+ фото в авторской обработке\n• мудборд и помощь со стилем",
        "от 45 000 ₽", "финальная цена — после брифа", "2–3 часа",
    )
    cov = await _seed_image("seed_ed1.jpg")
    if cov:
        await db.update_service(s1, cover_path=cov["file"], cover_thumb=cov["thumb"])

    s2 = await db.add_service(
        "Editorial / Commercial",
        "Съёмка для журналов, брендов и рекламных кампаний. Полный цикл: идея, продакшн, постобработка.\n• команда и продакшн под ключ\n• передача прав по договору\n• сроки от 7 дней",
        "от 120 000 ₽", "смета — после брифа", "1 съёмочный день",
    )
    cov = await _seed_image("seed_fa1.jpg")
    if cov:
        await db.update_service(s2, cover_path=cov["file"], cover_thumb=cov["thumb"])

    s3 = await db.add_service(
        "Свадебная съёмка",
        "Живые эмоции и киношная картинка. Беру не больше 10 свадеб в год.\n• до 10 часов в день свадьбы\n• 400+ фото в обработке\n• слайд-шоу и фотокнига опционально",
        "от 90 000 ₽", "предоплата 30%", "до 10 часов",
    )
    cov = await _seed_image("seed_wed1.jpg")
    if cov:
        await db.update_service(s3, cover_path=cov["file"], cover_thumb=cov["thumb"])

    # --- выставки ---
    await db.add_exhibition("Venice Biennale — Parallel Program", "Венеция, Италия", "2025", "Серия «Silence»")
    await db.add_exhibition("Paris Photo", "Париж, Франция", "2024", "Групповая выставка, Grand Palais")
    await db.add_exhibition("Unseen Amsterdam", "Амстердам, Нидерланды", "2023", "Сольная презентация серии «Muse»")
    await db.add_exhibition("IPA Awards — Best of Editorial", "Лос-Анджелес, США", "2024", "Top-3, категория Editorial")

    await db.set_setting("seeded", "1")
    log.info("demo content seeded")
