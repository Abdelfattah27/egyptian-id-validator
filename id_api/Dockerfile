# =========================================
# 1️⃣ Base Image
# =========================================
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =========================================
# 2️⃣ Install Poetry
# =========================================
ENV POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to avoid creating virtualenvs inside container
RUN poetry config virtualenvs.create false

# =========================================
# 3️⃣ Install Dependencies
# =========================================
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# =========================================
# 4️⃣ Copy Application Code
# =========================================
COPY . .

# =========================================
# 5️⃣ Expose Port & Run Server
# =========================================
EXPOSE 8000

# Collect static files (optional)
RUN python manage.py collectstatic --noinput || true
RUN python manage.py makemigrations --noinput || true
RUN python manage.py migrate --noinput || true

# Start Django with Gunicorn
CMD ["gunicorn", "id_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
