FROM python:3.12

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG SECRET_KEY
ARG ALLOWED_HOSTS
ARG DISCORDURL

ENV SECRET_KEY=${SECRET_KEY} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    DISCORDURL=${DISCORDURL}

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 80