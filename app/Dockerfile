# ===========================================
# 1. Base Image (Lightweight Python)
# ===========================================
FROM python:3.11-slim

# ===========================================
# 2. Set working directory
# ===========================================
WORKDIR /app

# ===========================================
# 3. Install system dependencies
# ===========================================
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ===========================================
# 4. Install Python deps (layer optimized)
# ===========================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ===========================================
# 5. Copy project files
# ===========================================
COPY . .

# ===========================================
# 6. Environment (runtime overrides allowed)
# ===========================================
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=run.py

# ===========================================
# 7. Expose Flask port
# ===========================================
EXPOSE 5000

# ===========================================
# 8. Gunicorn Command (optimized for 512 MB RAM)
# ===========================================
# - 1 worker only (512 MB limit)
# - threads=2 for concurrency
# - timeout to avoid container hangs
# ===========================================
CMD ["gunicorn", "--workers=1", "--threads=2", "--timeout=60", "--bind=0.0.0.0:5000", "run:app"]
