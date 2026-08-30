# Django + HTMX. Fără build de frontend: nu există bundler, nu există node.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

FROM base AS deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && pip install --no-cache-dir \
      "django>=5.2,<6.0" "django-allauth>=65.0" "django-htmx>=1.19" \
      "python-dotenv>=1.0" "pillow>=10.4" "psycopg[binary]>=3.2" \
      "dj-database-url>=2.2" "gunicorn>=23.0" "openpyxl>=3.1" \
 && apt-get purge -y build-essential libpq-dev && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

FROM deps AS app
COPY . .

# Utilizator neprivilegiat: procesul nu are nevoie de root, iar `private/`
# conține acte de identitate.
RUN useradd --system --uid 1001 --home-dir /home/app --create-home app \
 && mkdir -p /app/staticfiles /app/media /app/private \
 && chown -R app:app /app
USER app

# `collectstatic` la build: containerul de producție nu scrie în cod la pornire.
RUN DJANGO_COLLECTSTATIC=1 SECRET_KEY=build-only DEBUG=0 \
    ALLOWED_HOSTS=localhost python manage.py collectstatic --noinput

EXPOSE 8000
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", \
     "--access-logfile", "-", "--error-logfile", "-"]
