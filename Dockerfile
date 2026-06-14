# syntax=docker/dockerfile:1
#
# Multi-stage build for the hosted demo:
#   1) Node builds the React UI -> web/dist (fresh every deploy)
#   2) Python runtime serves the API and the built UI from one origin
#
# FastAPI prefers web/dist when present (else falls back to the zero-build
# frontend/), so the built React app is what gets served in production.

# ---------- Stage 1: build the React UI ----------
FROM node:22-alpine AS web
WORKDIR /web
# Install deps first (better layer caching). package-lock.json -> reproducible.
COPY web/package.json web/package-lock.json ./
RUN npm ci
# Build
COPY web/ ./
RUN npm run build      # outputs /web/dist

# ---------- Stage 2: Python runtime ----------
FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Backend dependencies (cached unless requirements change).
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Application code.
COPY backend/ ./backend/
# Zero-build fallback UI (tiny; used only if web/dist is ever absent).
COPY frontend/ ./frontend/
# Built React UI from stage 1. main.py resolves the repo root as the parent of
# backend/, so this lands at /app/web/dist exactly where it's expected.
COPY --from=web /web/dist ./web/dist

EXPOSE 8000
# Run from backend/ so the `app` package is importable. Respect $PORT if the
# host (Container Apps / Render / Fly / HF Spaces) injects one.
WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

