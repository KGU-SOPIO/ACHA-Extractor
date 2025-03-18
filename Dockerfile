FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    pkg-config \
    python3-dev \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG SECRET_KEY \
    ALLOWED_HOSTS \
    INFO_DISCORDURL \
    WARNING_DISCORDURL \
    LOG_PATH

ENV SECRET_KEY=${SECRET_KEY} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    INFO_DISCORDURL=${INFO_DISCORDURL} \
    WARNING_DISCORDURL=${WARNING_DISCORDURL} \
    LOG_PATH=${LOG_PATH}

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python manage.py collectstatic --noinput && \
    python manage.py makemigrations && \
    python manage.py migrate

EXPOSE 8000
