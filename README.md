# Wheelers Landing

Marketing site for **Wheelers** — a full-stack car-rental SaaS for the UAE.
FastAPI + Jinja2, recreated from the Claude Design pitch-deck mockup.

## Sections

1. **Hero** — positioning, dual CTAs, market stats, product dashboard
2. **Platform** — three pillars + six capability cards
3. **Pricing** — Starter / Basic / Pro subscription ladder
4. **Invest** — the $200k-for-20% raise, use-of-funds bars, market figures
5. **Contact** — instant contact form (demo / invest toggle) + founder card

## Run

```bash
uv sync
cp .env.example .env   # fill in SMTP credentials
uv run uvicorn main:app --reload
```

Then open http://127.0.0.1:8000.

## Contact form

The form posts to `POST /contact`, which relays the message through an
**external SMTP server** using the credentials in `.env` (see `.env.example`).
If `SMTP_HOST` is blank, submissions are accepted and logged but not emailed,
so the UI flow works out of the box during development.
