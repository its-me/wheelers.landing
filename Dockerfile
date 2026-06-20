FROM ghcr.io/its-me/debian:uv

WORKDIR /opt/app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY static/ static/
COPY templates/ templates/
COPY main.py .

EXPOSE 8000

CMD ["uv", "run", "granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "main:app"]
