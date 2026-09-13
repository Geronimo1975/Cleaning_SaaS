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
