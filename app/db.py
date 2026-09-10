"""Слой базы данных (SQLite через aiosqlite).

Сущности:
- settings: произвольные настройки сайта (имя, о себе, телефон, соцсети...)
- admins: дополнительные админы (помимо ADMIN_IDS из окружения)
- categories: разделы работ (Editorial, Fine Art, ...)
- albums: фотосеты / подкатегории внутри разделов
- photos: фотографии (привязка к альбому, услуге либо standalone-избранное)
- services: услуги с ценами
- exhibitions: выставки и награды
- leads: заявки из формы бронирования
"""

from __future__ import annotations

import time

import aiosqlite

from app.config import get_settings

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY,
    note TEXT NOT NULL DEFAULT '',
    added_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    sort INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    year TEXT NOT NULL DEFAULT '',
    cover_photo_id INTEGER NOT NULL DEFAULT 0,
    sort INTEGER NOT NULL DEFAULT 0,
    is_visible INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    thumb TEXT NOT NULL DEFAULT '',
    file_id TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    width INTEGER NOT NULL DEFAULT 0,
    height INTEGER NOT NULL DEFAULT 0,
    sort INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price TEXT NOT NULL DEFAULT '',
    price_note TEXT NOT NULL DEFAULT '',
    duration TEXT NOT NULL DEFAULT '',
    cover_path TEXT NOT NULL DEFAULT '',
    cover_thumb TEXT NOT NULL DEFAULT '',
    sort INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exhibitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    place TEXT NOT NULL DEFAULT '',
    year TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    sort INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
    service_title TEXT NOT NULL DEFAULT '',
    date_text TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    created_at INTEGER NOT NULL DEFAULT 0
);
"""


def _db_path() -> str:
    return str(get_settings().db_path)


async def init_db() -> None:
    get_settings().ensure_dirs()
    async with aiosqlite.connect(_db_path()) as con:
        await con.executescript(SCHEMA)
        await con.commit()


async def fetchall(query: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(_db_path()) as con:
        con.row_factory = aiosqlite.Row
        async with con.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def fetchone(query: str, params: tuple = ()) -> dict | None:
    rows = await fetchall(query, params)
    return rows[0] if rows else None


async def execute(query: str, params: tuple = ()) -> int:
    async with aiosqlite.connect(_db_path()) as con:
        cur = await con.execute(query, params)
        await con.commit()
        return cur.lastrowid or 0


def _now() -> int:
    return int(time.time())


async def _next_sort(table: str, where: str = "1=1", params: tuple = ()) -> int:
    row = await fetchone(f"SELECT COALESCE(MAX(sort), 0) AS m FROM {table} WHERE {where}", params)
    return (row["m"] if row else 0) + 1


async def _move(table: str, item_id: int, direction: str, where: str = "1=1", params: tuple = ()) -> bool:
    """Меняет местами сортировку элемента с соседом (up/down)."""
    rows = await fetchall(f"SELECT id, sort FROM {table} WHERE {where} ORDER BY sort, id", params)
    idx = next((i for i, r in enumerate(rows) if r["id"] == item_id), None)
    if idx is None:
        return False
    j = idx - 1 if direction == "up" else idx + 1
    if j < 0 or j >= len(rows):
        return False
    await execute(f"UPDATE {table} SET sort=? WHERE id=?", (rows[j]["sort"], item_id))
    await execute(f"UPDATE {table} SET sort=? WHERE id=?", (rows[idx]["sort"], rows[j]["id"]))
    return True


# ---------------------------------------------------------------- settings
async def get_setting(key: str, default: str = "") -> str:
    row = await fetchone("SELECT value FROM settings WHERE key=?", (key,))
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    await execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


async def all_settings() -> dict[str, str]:
    rows = await fetchall("SELECT key, value FROM settings")
    return {r["key"]: r["value"] for r in rows}


# ---------------------------------------------------------------- admins
async def list_admin_ids() -> list[int]:
    ids = set(get_settings().admin_ids)
    rows = await fetchall("SELECT user_id FROM admins")
    ids.update(r["user_id"] for r in rows)
    return sorted(ids)


async def is_admin(user_id: int | None) -> bool:
    if not user_id:
        return False
    return user_id in await list_admin_ids()


async def add_admin(user_id: int, note: str = "") -> None:
    await execute("INSERT OR IGNORE INTO admins(user_id, note, added_at) VALUES(?, ?, ?)", (user_id, note, _now()))


async def remove_admin(user_id: int) -> None:
    await execute("DELETE FROM admins WHERE user_id=?", (user_id,))


# ---------------------------------------------------------------- categories
async def list_categories() -> list[dict]:
    return await fetchall(
        """SELECT c.*,
           (SELECT COUNT(*) FROM albums a WHERE a.category_id=c.id) AS albums_count,
           (SELECT COUNT(*) FROM photos p JOIN albums a ON a.id=p.album_id WHERE a.category_id=c.id) AS photos_count
           FROM categories c ORDER BY c.sort, c.id"""
    )


async def get_category(cat_id: int) -> dict | None:
    return await fetchone("SELECT * FROM categories WHERE id=?", (cat_id,))


async def add_category(title: str, subtitle: str = "") -> int:
    return await execute(
        "INSERT INTO categories(title, subtitle, sort, created_at) VALUES(?, ?, ?, ?)",
        (title, subtitle, await _next_sort("categories"), _now()),
    )


async def update_category(cat_id: int, title: str, subtitle: str) -> None:
    await execute("UPDATE categories SET title=?, subtitle=? WHERE id=?", (title, subtitle, cat_id))


async def delete_category(cat_id: int) -> bool:
    """Удаление только если нет альбомов. True — удалено."""
    row = await fetchone("SELECT COUNT(*) AS c FROM albums WHERE category_id=?", (cat_id,))
    if row and row["c"] > 0:
        return False
    await execute("DELETE FROM categories WHERE id=?", (cat_id,))
    return True


async def move_category(cat_id: int, direction: str) -> bool:
    return await _move("categories", cat_id, direction)


# ---------------------------------------------------------------- albums
async def list_albums(category_id: int | None = None) -> list[dict]:
    if category_id is None:
        return await fetchall("SELECT * FROM albums ORDER BY sort, id")
    return await fetchall("SELECT * FROM albums WHERE category_id=? ORDER BY sort, id", (category_id,))


async def get_album(album_id: int) -> dict | None:
    return await fetchone("SELECT * FROM albums WHERE id=?", (album_id,))


async def add_album(category_id: int, title: str, description: str = "", location: str = "", year: str = "") -> int:
    return await execute(
        """INSERT INTO albums(category_id, title, description, location, year, sort, created_at)
           VALUES(?, ?, ?, ?, ?, ?, ?)""",
        (category_id, title, description, location, year, await _next_sort("albums", "category_id=?", (category_id,)), _now()),
    )


async def update_album(album_id: int, **fields) -> None:
    allowed = {"category_id", "title", "description", "location", "year", "cover_photo_id", "is_visible"}
    sets = [f"{k}=?" for k in fields if k in allowed]
    if not sets:
        return
    await execute(f"UPDATE albums SET {', '.join(sets)} WHERE id=?", tuple(fields[k] for k in fields if k in allowed) + (album_id,))


async def delete_album(album_id: int) -> list[str]:
    """Удаляет альбом и возвращает пути файлов для удаления с диска."""
    rows = await fetchall("SELECT path, thumb FROM photos WHERE album_id=?", (album_id,))
    await execute("DELETE FROM albums WHERE id=?", (album_id,))
    paths: list[str] = []
    for r in rows:
        paths += [r["path"], r["thumb"]]
    return [p for p in paths if p]


async def move_album(album_id: int, direction: str) -> bool:
    album = await get_album(album_id)
    if not album:
        return False
    return await _move("albums", album_id, direction, "category_id=?", (album["category_id"],))


# ---------------------------------------------------------------- photos
async def list_photos(
    album_id: int | None = None,
    service_id: int | None = None,
    standalone: bool = False,
) -> list[dict]:
    if album_id is not None:
        return await fetchall("SELECT * FROM photos WHERE album_id=? ORDER BY sort, id", (album_id,))
    if service_id is not None:
        return await fetchall("SELECT * FROM photos WHERE service_id=? ORDER BY sort, id", (service_id,))
    if standalone:
        return await fetchall("SELECT * FROM photos WHERE album_id IS NULL AND service_id IS NULL ORDER BY sort, id")
    return await fetchall("SELECT * FROM photos ORDER BY sort, id")


async def get_photo(photo_id: int) -> dict | None:
    return await fetchone("SELECT * FROM photos WHERE id=?", (photo_id,))


async def add_photo(
    path: str,
    thumb: str = "",
    file_id: str = "",
    caption: str = "",
    album_id: int | None = None,
    service_id: int | None = None,
    width: int = 0,
    height: int = 0,
) -> int:
    where, params = "album_id IS NULL AND service_id IS NULL", ()
    if album_id is not None:
        where, params = "album_id=?", (album_id,)
    elif service_id is not None:
        where, params = "service_id=?", (service_id,)
    return await execute(
        """INSERT INTO photos(album_id, service_id, path, thumb, file_id, caption, width, height, sort, created_at)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (album_id, service_id, path, thumb, file_id, caption, width, height, await _next_sort("photos", where, params), _now()),
    )


async def update_photo_caption(photo_id: int, caption: str) -> None:
    await execute("UPDATE photos SET caption=? WHERE id=?", (caption, photo_id))


async def delete_photo(photo_id: int) -> list[str]:
    photo = await get_photo(photo_id)
    if not photo:
        return []
    await execute("DELETE FROM photos WHERE id=?", (photo_id,))
    # сбрасываем обложку альбома, если указывала на это фото
    await execute("UPDATE albums SET cover_photo_id=0 WHERE cover_photo_id=?", (photo_id,))
    return [p for p in (photo["path"], photo["thumb"]) if p]


async def path_refs_count(path: str) -> int:
    row = await fetchone("SELECT COUNT(*) AS c FROM photos WHERE path=? OR thumb=?", (path, path))
    return row["c"] if row else 0


async def move_photo(photo_id: int, direction: str) -> bool:
    photo = await get_photo(photo_id)
    if not photo:
        return False
    if photo["album_id"] is not None:
        return await _move("photos", photo_id, direction, "album_id=?", (photo["album_id"],))
    if photo["service_id"] is not None:
        return await _move("photos", photo_id, direction, "service_id=?", (photo["service_id"],))
    return await _move("photos", photo_id, direction, "album_id IS NULL AND service_id IS NULL")


async def count_photos() -> int:
    row = await fetchone("SELECT COUNT(*) AS c FROM photos")
    return row["c"] if row else 0


async def find_photo_by_path(filename: str) -> dict | None:
    return await fetchone("SELECT * FROM photos WHERE path=? OR thumb=?", (filename, filename))


# ---------------------------------------------------------------- services
async def list_services(active_only: bool = False) -> list[dict]:
    if active_only:
        return await fetchall("SELECT * FROM services WHERE is_active=1 ORDER BY sort, id")
    return await fetchall("SELECT * FROM services ORDER BY sort, id")


async def get_service(service_id: int) -> dict | None:
    return await fetchone("SELECT * FROM services WHERE id=?", (service_id,))


async def add_service(title: str, description: str = "", price: str = "", price_note: str = "", duration: str = "") -> int:
    return await execute(
        """INSERT INTO services(title, description, price, price_note, duration, sort, created_at)
           VALUES(?, ?, ?, ?, ?, ?, ?)""",
        (title, description, price, price_note, duration, await _next_sort("services"), _now()),
    )


async def update_service(service_id: int, **fields) -> None:
    allowed = {"title", "description", "price", "price_note", "duration", "cover_path", "cover_thumb", "is_active"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    await execute(f"UPDATE services SET {sets} WHERE id=?", tuple(fields.values()) + (service_id,))


async def delete_service(service_id: int) -> list[str]:
    rows = await fetchall("SELECT path, thumb FROM photos WHERE service_id=?", (service_id,))
    svc = await get_service(service_id)
    await execute("DELETE FROM services WHERE id=?", (service_id,))
    paths: list[str] = []
    for r in rows:
        paths += [r["path"], r["thumb"]]
    if svc:
        paths += [svc["cover_path"], svc["cover_thumb"]]
    return [p for p in paths if p]


async def move_service(service_id: int, direction: str) -> bool:
    return await _move("services", service_id, direction)


# ---------------------------------------------------------------- exhibitions
async def list_exhibitions() -> list[dict]:
    return await fetchall("SELECT * FROM exhibitions ORDER BY sort, id")


async def get_exhibition(ex_id: int) -> dict | None:
    return await fetchone("SELECT * FROM exhibitions WHERE id=?", (ex_id,))


async def add_exhibition(title: str, place: str = "", year: str = "", description: str = "") -> int:
    return await execute(
        "INSERT INTO exhibitions(title, place, year, description, sort, created_at) VALUES(?, ?, ?, ?, ?, ?)",
        (title, place, year, description, await _next_sort("exhibitions"), _now()),
    )


async def update_exhibition(ex_id: int, **fields) -> None:
    allowed = {"title", "place", "year", "description"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    await execute(f"UPDATE exhibitions SET {sets} WHERE id=?", tuple(fields.values()) + (ex_id,))


async def delete_exhibition(ex_id: int) -> None:
    await execute("DELETE FROM exhibitions WHERE id=?", (ex_id,))


async def move_exhibition(ex_id: int, direction: str) -> bool:
    return await _move("exhibitions", ex_id, direction)


# ---------------------------------------------------------------- leads
async def add_lead(name: str, contact: str, service_id: int | None, service_title: str, date_text: str, message: str) -> int:
    return await execute(
        """INSERT INTO leads(name, contact, service_id, service_title, date_text, message, status, created_at)
           VALUES(?, ?, ?, ?, ?, ?, 'new', ?)""",
        (name, contact, service_id, service_title, date_text, message, _now()),
    )


async def list_leads(status: str | None = None, limit: int = 20) -> list[dict]:
    if status:
        return await fetchall("SELECT * FROM leads WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit))
    return await fetchall("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,))


async def get_lead(lead_id: int) -> dict | None:
    return await fetchone("SELECT * FROM leads WHERE id=?", (lead_id,))


async def set_lead_status(lead_id: int, status: str) -> None:
    await execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))


async def count_new_leads() -> int:
    row = await fetchone("SELECT COUNT(*) AS c FROM leads WHERE status='new'")
    return row["c"] if row else 0
