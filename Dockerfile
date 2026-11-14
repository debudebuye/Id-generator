FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies:
#  - tesseract-ocr: required by pytesseract (found on PATH on Linux)
#  - libgl1/libglib2.0-0: runtime libs for OpenCV
#  - libgomp1: runtime lib required by PyTorch (easyocr)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn==21.2.0

COPY . .

RUN useradd --uid 1000 --create-home appuser \
    && mkdir -p /app/uploads /app/logs /app/temp /app/data /app/telegram_bot/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Cloud Run sets $PORT (defaults to 8080) and expects the container to listen on
# it, so this needs shell-form expansion rather than the exec-form array above.
# Single worker: the ID-generation pipeline writes to fixed filenames
# (photo_temp.png, qr_temp.png, fcn_barcode.png) on local disk rather than
# per-request paths, so two requests running at once on the same container can
# clobber each other's files - that's pre-existing, not introduced by the
# webhook change. Pair this with `gcloud run deploy --concurrency=1` so Cloud
# Run never sends a container a second request while the first is still
# generating; scale out with --max-instances instead of in-container
# concurrency until that pipeline is made per-request-safe.
CMD exec gunicorn -w 1 -b 0.0.0.0:${PORT:-8080} --timeout 180 app:app
