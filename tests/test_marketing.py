"""Paginile de marketing: publice, în germană, formularul de contact trimite email."""

import pytest
from django.core import mail

PAGES = ["/", "/leistungen/", "/fuer-betriebe/", "/fuer-reinigungskraefte/",
         "/fuer-auftraggeber/", "/kontakt/"]


@pytest.mark.django_db
@pytest.mark.parametrize("url", PAGES)
def test_pagina_publica_raspunde_200(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert b'lang="de"' in response.content
    assert b"Jetzt starten" in response.content


@pytest.mark.django_db
def test_sitemap_contine_paginile_statice(client):
    response = client.get("/sitemap-static.xml")
    assert response.status_code == 200
    assert b"/fuer-betriebe/" in response.content


@pytest.mark.django_db
def test_kontakt_trimite_email(client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.OPERATOR = {**settings.OPERATOR, "email": "op@example.de"}
    response = client.post("/kontakt/", {
        "name": "Max", "email": "max@example.de", "subject": "Frage",
        "message": "Hallo", "privacy": "on",
    })
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["op@example.de"]
    assert "Frage" in mail.outbox[0].subject


@pytest.mark.django_db
def test_kontakt_fara_consimtamant_nu_trimite(client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    response = client.post("/kontakt/", {
        "name": "Max", "email": "max@example.de", "subject": "Frage", "message": "Hallo",
    })
    assert response.status_code == 200
    assert mail.outbox == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url", ["/accounts/login/", "/accounts/signup/", "/accounts/password/reset/"]
)
def test_paginile_allauth_folosesc_layoutul_public(client, url):
    """Login/signup trec prin base.html: header-ul public și cardul .entrance."""
    response = client.get(url)
    assert response.status_code == 200
    assert b'class="site-head"' in response.content
    assert b'class="entrance"' in response.content


@pytest.mark.django_db
def test_blog_si_articolul_raspund_200(client):
    assert client.get("/blog/").status_code == 200
    response = client.get("/blog/reinigungsplan-vorlage/")
    assert response.status_code == 200
    assert b"Vorlage anfordern" in response.content


@pytest.mark.django_db
def test_descarcarea_sablonului_trimite_linkul_pe_email(client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    response = client.post(
        "/blog/reinigungsplan-vorlage/", {"email": "max@example.de", "privacy": "on"}
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "reinigungsplan-vorlage.xlsx" in mail.outbox[0].body
    # static-ul e servit de Nginx, nu de Django; verificăm doar că fișierul e în repo
    assert (settings.BASE_DIR / "static/downloads/reinigungsplan-vorlage.xlsx").is_file()
