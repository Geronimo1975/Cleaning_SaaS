from pathlib import Path

import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-not-a-secret")
DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
if DEBUG:
    # `testserver` e gazda clientului de test Django. Nu are ce căuta într-o
    # listă implicită de producție.
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    # third party
    "allauth",
    "allauth.account",
    "django_htmx",
    # local
    "apps.common",
    "apps.accounts",
    "apps.geo",
    "apps.taxonomy",
    "apps.jobs",
    "apps.catalog",
    "apps.contracts",
    "apps.planning",
    "apps.devices",
    "apps.marketplace",
    "apps.cooperative",
    "apps.legal",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.accounts.middleware.ActiveAccountMiddleware",
    "apps.legal.publication.PublicationGateMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboard.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Postgres e baza de date a proiectului; SQLite e doar comoditate locală.
# Ordinea contează: implicitul trebuie să fie ce rulează în producție, altfel
# diferențele (constrângeri, tipuri, tranzacții) apar abia la deploy.
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- allauth: login pe email, fără username ---------------------------
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m"}
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Documentele de verificare NU stau în MEDIA_ROOT.
#
# MEDIA_ROOT e servit direct de Nginx, fără să treacă prin Django — deci fără
# nicio verificare de drepturi. Un act de identitate sau un Führungszeugnis
# ajuns acolo e public pentru oricine îi află URL-ul. Storage separat, în afara
# rădăcinii servite, plus o vedere care verifică proprietarul.
PRIVATE_STORAGE_ROOT = Path(os.getenv("PRIVATE_STORAGE_ROOT", BASE_DIR / "private"))

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "private": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(PRIVATE_STORAGE_ROOT)},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Datele operatorului pentru Impressum (§5 TMG) și Datenschutzerklärung.
# Nu se inventează: cât timp lipsesc, paginile o spun explicit.
OPERATOR = {
    "name": os.getenv("OPERATOR_NAME", ""),
    "legal_form": os.getenv("OPERATOR_LEGAL_FORM", ""),
    "street": os.getenv("OPERATOR_STREET", ""),
    "postal_code": os.getenv("OPERATOR_POSTAL_CODE", ""),
    "city": os.getenv("OPERATOR_CITY", ""),
    "email": os.getenv("OPERATOR_EMAIL", ""),
    "phone": os.getenv("OPERATOR_PHONE", ""),
    "represented_by": os.getenv("OPERATOR_REPRESENTED_BY", ""),
    "register_court": os.getenv("OPERATOR_REGISTER_COURT", ""),
    "register_number": os.getenv("OPERATOR_REGISTER_NUMBER", ""),
    "vat_id": os.getenv("OPERATOR_VAT_ID", ""),
    "supervisory_authority": os.getenv("OPERATOR_SUPERVISORY_AUTHORITY", ""),
    "dpo_email": os.getenv("OPERATOR_DPO_EMAIL", ""),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@localhost")
if os.getenv("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if not DEBUG:
    # Aplicația stă în spatele Nginx, care termină TLS. Fără antetul de mai jos
    # Django vede http, iar SECURE_SSL_REDIRECT intră în buclă infinită.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    # Django cere originile de încredere explicit pentru POST peste https.
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

    if SECRET_KEY == "dev-only-not-a-secret":
        raise RuntimeError("SECRET_KEY nu a fost setat în producție.")

# Google Indexing API — calea către fișierul JSON al service account-ului.
# Gol = notificările se acumulează în coadă și nu se trimit (dev/test).
GOOGLE_INDEXING_CREDENTIALS = os.getenv("GOOGLE_INDEXING_CREDENTIALS", "")

# --- Cache -----------------------------------------------------------------
#
# Fără Redis configurat, cache local în proces. E suficient pentru un singur
# container, dar NU e partajat: cu mai multe procese gunicorn, fiecare are
# propriul cache. Orice se bazează pe cache partajat (rate limiting, invalidare
# între workeri) are nevoie de REDIS_URL.
if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["REDIS_URL"],
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cleaning-saas",
        }
    }

# --- Logging ---------------------------------------------------------------
#
# Totul pe stdout, într-o singură linie per eveniment: containerele nu au
# fișiere de log, iar Docker/journald colectează stdout. Nivelul se schimbă
# din mediu, fără deploy.
#
# `django.db.backends` rămâne pe WARNING chiar și la DEBUG global — pe DEBUG
# ar loga fiecare interogare SQL și ar face restul ilizibil. Se pornește
# explicit cu SQL_DEBUG=1 când chiar cauți un N+1.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        # 4xx-urile aplicației sunt zgomot; 5xx-urile sunt incidente.
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if os.getenv("SQL_DEBUG") == "1" else "WARNING",
            "propagate": False,
        },
        # Codul propriu: implicit INFO, ca publicările, semnăturile și golirea
        # cozii de indexare să lase urmă.
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# --- Error tracking --------------------------------------------------------
#
# Opțional și izolat: fără DSN sau fără pachetul instalat, aplicația pornește
# neschimbată. `send_default_pii=False` e obligatoriu aici — un raport de
# eroare care cară adrese și telefoane de prestatori e o problemă DSGVO, nu un
# ajutor la depanare.
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
        )
    except ImportError:  # pachetul e extra opțional
        import logging

        logging.getLogger("apps").warning(
            "SENTRY_DSN e setat, dar sentry-sdk nu e instalat. "
            'Instalează extra-ul: uv pip install -e ".[monitoring]"'
        )

# Cât timp poate sta o notificare de indexare în coadă înainte ca /healthz/ să
# o considere blocată. Serviciul `cron` golește coada la 15 minute.
INDEXING_STALE_MINUTES = int(os.getenv("INDEXING_STALE_MINUTES", "60"))
