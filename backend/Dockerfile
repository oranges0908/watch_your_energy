# ── Stage 1: Build Flutter web ────────────────────────────────────────────────
FROM ghcr.io/cirruslabs/flutter:stable AS flutter-builder

WORKDIR /frontend
COPY frontend/ .
RUN flutter pub get && flutter build web --release

# ── Stage 2: Python backend + static files ────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Embed the Flutter web build so FastAPI can serve it
COPY --from=flutter-builder /frontend/build/web ./static

# Default port; overridden by $PORT at runtime (Railway sets this automatically)
ENV PORT=8000

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
