"""
Paginile legale.

Regula pe care o apără: un Impressum incomplet trebuie să SPUNĂ că e incomplet.
§5 TMG cere identitate exactă — o pagină care pretinde că e în regulă cu date
lipsă e mai rea decât o pagină care lipsește.
"""

import pytest


@pytest.mark.django_db
class TestLegalPages:
    @pytest.mark.parametrize(
        "url", ["/impressum/", "/datenschutz/", "/agb/"]
    )
    def test_paginile_sunt_publice(self, client, url):
        assert client.get(url).status_code == 200

    def test_impressumul_neconfigurat_se_autodenunta(self, client, settings):
        settings.OPERATOR = {}
        response = client.get("/impressum/")
        assert b"nicht rechtsg" in response.content
        assert b"5 TMG" in response.content

    def test_impressumul_configurat_afiseaza_datele(self, client, settings):
        settings.OPERATOR = {
            "name": "Nordclean", "legal_form": "GmbH", "street": "Ulzburger Str. 40",
            "postal_code": "22846", "city": "Norderstedt", "email": "info@example.de",
            "phone": "+49 40 1234567", "represented_by": "Klaus Meyer",
            "vat_id": "DE123456789",
        }
        response = client.get("/impressum/")
        assert b"nicht rechtsg" not in response.content
        assert b"Ulzburger Str. 40" in response.content
        assert b"DE123456789" in response.content

    def test_datenschutz_declara_documentele_private(self, client):
        response = client.get("/datenschutz/")
        assert b"Verifizierungsdokumente" in response.content
        assert b"getrennt" in response.content

    def test_agb_explica_cine_e_angajator_la_minijob(self, client):
        response = client.get("/agb/")
        assert b"Minijob-Zentrale" in response.content
        assert b"Haushaltsscheck" in response.content

    def test_agb_mentioneaza_35a_si_plata_bancara(self, client):
        response = client.get("/agb/")
        assert b"35a EStG" in response.content
        assert b"Barzahlung ist nicht absetzbar" in response.content


OPERATOR_COMPLET = {
    "name": "Nordclean", "legal_form": "GmbH", "street": "Ulzburger Str. 40",
    "postal_code": "22846", "city": "Norderstedt", "email": "info@example.de",
    "phone": "+49 40 1234567", "represented_by": "Klaus Meyer",
}


@pytest.mark.django_db
class TestPublicationGate:
    """
    Indexarea nu e o setare separată, pe care cineva s-o uite pornită. E derivată
    din completitudinea Impressum-ului: un site german public fără §5 TMG e motiv
    de Abmahnung, iar aici tocmai conținutul indexat ar fi cel care atrage
    problema.
    """

    def test_fara_operator_totul_e_noindex(self, client, settings):
        settings.OPERATOR = {}
        response = client.get("/impressum/")
        assert response.headers["X-Robots-Tag"] == "noindex, nofollow"

    def test_fara_operator_robots_blocheaza_tot(self, client, settings):
        settings.OPERATOR = {}
        body = client.get("/robots.txt").content.decode()
        assert "Disallow: /\n" in body
        assert "Sitemap:" not in body

    def test_cu_operator_site_ul_se_deschide(self, client, settings):
        settings.OPERATOR = OPERATOR_COMPLET
        response = client.get("/impressum/")
        assert "X-Robots-Tag" not in response.headers
        body = client.get("/robots.txt").content.decode()
        assert "Disallow: /dashboard/" in body
        assert "Sitemap:" in body
        assert "Disallow: /\n" not in body

    def test_google_nu_e_notificat_fara_impressum(self, settings, db):
        settings.OPERATOR = {}
        from apps.jobs.indexing import flush

        report = flush()
        assert "operator nedeclarat" in report["skipped"]
        assert report["sent"] == 0

    def test_poarta_se_deschide_singura_la_completare(self, settings, db):
        from apps.jobs.indexing import flush

        settings.OPERATOR = OPERATOR_COMPLET
        report = flush()
        assert "operator nedeclarat" not in str(report.get("skipped", ""))
