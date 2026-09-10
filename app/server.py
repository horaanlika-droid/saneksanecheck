"""HTTP-сервер: JSON API для мини-приложения + раздача фронтенда и фото."""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db
from app.config import get_settings

log = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

PUBLIC_SETTINGS = [
    "brand_name", "tagline", "about", "facts", "city", "phone",
    "telegram", "whatsapp", "instagram", "behance", "email",
    "experience_years", "shoots_count", "countries_count",
    "currency", "booking_enabled", "avatar_path", "avatar_thumb",
    "hero_path", "hero_thumb",
]

# простой антиспам для формы: contact -> timestamp последней заявки
_last_booking: dict[str, float] = {}


def _photo_json(row: dict) -> dict:
    return {
        "id": row["id"],
        "url": f"/uploads/{row['path']}" if row["path"] else "",
        "thumb": f"/uploads/{row['thumb']}" if row["thumb"] else "",
        "caption": row.get("caption", ""),
        "w": row.get("width", 0),
        "h": row.get("height", 0),
    }


def _upload(name: str) -> str:
    return f"/uploads/{name}" if name else ""


class BookingIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    contact: str = Field(min_length=3, max_length=200)
    service_id: int | None = None
    date_text: str = Field(default="", max_length=100)
    message: str = Field(default="", max_length=2000)


def create_app() -> FastAPI:
    app = FastAPI(title="Photographer Portfolio", docs_url=None, redoc_url=None)

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.get("/api/site")
    async def api_site():
        """Всё для первого экрана: настройки, разделы, услуги, выставки, избранное."""
        settings_all = await db.all_settings()
        settings = {k: settings_all.get(k, "") for k in PUBLIC_SETTINGS}
        settings["avatar_url"] = _upload(settings.pop("avatar_path"))
        settings["avatar_thumb"] = _upload(settings.pop("avatar_thumb"))
        settings["hero_url"] = _upload(settings.pop("hero_path"))
        settings["hero_thumb"] = _upload(settings.pop("hero_thumb"))

        categories = []
        for cat in await db.list_categories():
            albums = []
            for alb in await db.list_albums(cat["id"]):
                if not alb["is_visible"]:
                    continue
                photos = await db.list_photos(album_id=alb["id"])
                cover = next((p for p in photos if p["id"] == alb["cover_photo_id"]), None) or (photos[0] if photos else None)
                albums.append({
                    "id": alb["id"],
                    "title": alb["title"],
                    "description": alb["description"],
                    "location": alb["location"],
                    "year": alb["year"],
                    "count": len(photos),
                    "cover": _photo_json(cover) if cover else None,
                })
            categories.append({
                "id": cat["id"],
                "title": cat["title"],
                "subtitle": cat["subtitle"],
                "albums": albums,
            })

        services = []
        for svc in await db.list_services(active_only=True):
            photos = await db.list_photos(service_id=svc["id"])
            services.append({
                "id": svc["id"],
                "title": svc["title"],
                "description": svc["description"],
                "price": svc["price"],
                "price_note": svc["price_note"],
                "duration": svc["duration"],
                "cover": _upload(svc["cover_path"]),
                "cover_thumb": _upload(svc["cover_thumb"]),
                "photos": [_photo_json(p) for p in photos],
            })

        standalone = [_photo_json(p) for p in await db.list_photos(standalone=True)]
        exhibitions = await db.list_exhibitions()

        return {
            "settings": settings,
            "categories": categories,
            "services": services,
            "exhibitions": exhibitions,
            "selected": standalone,
        }

    @app.get("/api/album/{album_id}")
    async def api_album(album_id: int):
        alb = await db.get_album(album_id)
        if not alb or not alb["is_visible"]:
            raise HTTPException(404, "album not found")
        photos = await db.list_photos(album_id=album_id)
        cat = await db.get_category(alb["category_id"])
        return {
            "id": alb["id"],
            "title": alb["title"],
            "description": alb["description"],
            "location": alb["location"],
            "year": alb["year"],
            "category": cat["title"] if cat else "",
            "photos": [_photo_json(p) for p in photos],
        }

    @app.post("/api/booking")
    async def api_booking(data: BookingIn, request: Request):
        settings = await db.all_settings()
        if settings.get("booking_enabled", "1") != "1":
            raise HTTPException(403, "booking disabled")

        key = f"{request.client.host if request.client else ''}|{data.contact.strip().lower()}" if request.client else data.contact
        now = time.time()
        if now - _last_booking.get(key, 0) < 120:
            raise HTTPException(429, "too many requests, try later")
        _last_booking[key] = now

        service_title = ""
        if data.service_id:
            svc = await db.get_service(data.service_id)
            if svc:
                service_title = svc["title"]

        lead_id = await db.add_lead(
            data.name.strip(), data.contact.strip(),
            data.service_id, service_title,
            data.date_text.strip(), data.message.strip(),
        )

        # уведомляем админов в бота (fire-and-forget)
        try:
            from app.bot.notify import notify_new_lead
            await notify_new_lead(lead_id)
        except Exception:
            log.exception("lead notify failed")

        return {"ok": True, "id": lead_id}

    @app.get("/uploads/{filename}")
    async def uploads(filename: str):
        """Отдача фото. Если файла нет на диске (напр. после переезда) —
        восстанавливаем его из Telegram по сохранённому file_id и кэшируем."""
        safe = Path(filename).name
        if not safe or safe.startswith("."):
            raise HTTPException(404)
        fpath = get_settings().upload_dir / safe
        if fpath.exists():
            return FileResponse(fpath, media_type="image/jpeg")
        # самовосстановление из Telegram
        row = await db.find_photo_by_path(safe)
        file_id = (row.get("file_id") or "") if row else ""
        if not file_id:
            raise HTTPException(404)
        try:
            from app.bot.notify import get_bot
            bot = get_bot()
            if bot is None:
                raise HTTPException(404)
            buf = io.BytesIO()
            await bot.download(file_id, destination=buf)
            data = buf.getvalue()
            if not data:
                raise HTTPException(404)
            # сохраняем оригинал; превью пересоздастся при следующем обращении
            from app.images import process_image_bytes
            if safe.endswith("_t.jpg"):
                fpath.write_bytes(data)
            else:
                try:
                    info = process_image_bytes(data, get_settings().upload_dir)
                    saved = get_settings().upload_dir / info["file"]
                    fpath.write_bytes(saved.read_bytes())
                    saved.unlink(missing_ok=True)
                except Exception:
                    fpath.write_bytes(data)
            return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")
        except HTTPException:
            raise
        except Exception:
            log.exception("media restore failed for %s", safe)
            raise HTTPException(404)

    # фронтенд
    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

        @app.get("/", response_class=HTMLResponse)
        async def index():
            return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    return app
