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
    && mkdir -p /app/uploads /app/logs /app/temp /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
