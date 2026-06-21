"""Wheelers landing page — FastAPI + Jinja2.

Serves the marketing site and handles the contact form, relaying submissions
to an external SMTP server using credentials from the environment / .env file.
"""
from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("wheelers")


class Settings(BaseSettings):
    """SMTP + site configuration, loaded from environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False          # implicit TLS (e.g. port 465)
    smtp_start_tls: bool = True         # STARTTLS upgrade (e.g. port 587)

    mail_from: str = "Wheelers <noreply@wheele.rs>"
    contact_to: str = "sergeykanafyev@gmail.com"

    @property
    def configured(self) -> bool:
        return bool(self.smtp_host)


settings = Settings()

# Brand palette sampled from the pitch deck / product UI.
BRAND = {
    "blue": "#1B3D97",
    "mint": "#B7EBE1",
    "coral": "#DB8C6A",
}

# Right-rail scroll-spy dots / nav anchors.
NAV = [
    {"href": "#top", "label": "Home"},
    {"href": "#product", "label": "Product"},
    {"href": "#pricing", "label": "Pricing"},
    {"href": "#invest", "label": "Invest"},
    {"href": "#contact", "label": "Contact"},
]

# Product capability cards.
CAPS = [
    {"title": "Fleet Management",
     "desc": "Real-time fleet status, vehicle utilization, and proactive maintenance schedules."},
    {"title": "Customer Portal & Chat",
     "desc": "Order tracking, rental history, and direct chat with the operator."},
    {"title": "Tolls & Fines Integration",
     "desc": "Smart invoicing and real-time updates for UAE tolls and traffic fines."},
    {"title": "Full Mobile Experience",
     "desc": "A full-fledged mobile experience for both Android and iOS."},
    {"title": "Integrated Insurance",
     "desc": "Insurance options are embedded directly into the core rental flow."},
    {"title": "AI-Driven Productivity",
     "desc": "Platform-wide AI agents and 24/7 automated support chatbots."},
]

class _ProxySchemeMiddleware:
    """Propagate X-Forwarded-Proto so url_for generates https:// behind a TLS proxy."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope["headers"])
            proto = headers.get(b"x-forwarded-proto", b"").decode().strip()
            if proto:
                scope["scheme"] = proto
        await self.app(scope, receive, send)


app = FastAPI(title="Wheelers Landing")
app.add_middleware(_ProxySchemeMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    return FileResponse("static/sitemap.xml", media_type="application/xml")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"brand": BRAND, "nav": NAV, "caps": CAPS},
    )


async def send_contact_email(name: str, email: str, message: str) -> None:
    """Relay a contact submission through the configured SMTP server."""
    msg = EmailMessage()
    sender = f"{name} <{email}>" if name else email
    msg["Subject"] = f"[Wheelers] New enquiry from {sender}"
    msg["From"] = settings.mail_from
    msg["To"] = settings.contact_to
    if email:
        msg["Reply-To"] = email
    msg.set_content(message or "(no message)")

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        use_tls=settings.smtp_use_tls,
        start_tls=settings.smtp_start_tls,
    )


@app.post("/contact")
async def contact(
    name: str = Form(""),
    email: EmailStr = Form(...),
    message: str = Form(""),
):
    if not settings.configured:
        # No SMTP configured yet — accept the submission so the UI flow works,
        # but make it explicit in the logs that nothing was sent.
        logger.warning("Contact form submitted but SMTP is not configured; email not sent. From=%s", email)
        return JSONResponse({"ok": True, "delivered": False})

    try:
        await send_contact_email(name, str(email), message)
    except Exception:  # noqa: BLE001 — surface a clean error to the client, log the detail
        logger.exception("Failed to relay contact email")
        return JSONResponse(
            {"ok": False, "error": "We couldn't send your message right now. Please email us directly."},
            status_code=502,
        )

    return JSONResponse({"ok": True, "delivered": True})
