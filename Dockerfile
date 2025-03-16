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

ARG SECRET_KEY
ARG ALLOWED_HOSTS
ARG INFO_DISCORDURL
ARG WARNING_DISCORDURL

ENV SECRET_KEY=${SECRET_KEY} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    INFO_DISCORDURL=${INFO_DISCORDURL} \
    WARNING_DISCORDURL=${WARNING_DISCORDURL}

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 80
