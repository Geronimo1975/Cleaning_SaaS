"""Verificările legale trebuie să BLOCHEZE, nu doar să avertizeze."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.contracts.models import (
    ContractDraft,
    ContractType,
    DraftStatus,
    EngagementModel,
    MinijobThreshold,
    WageFloor,
)
from apps.contracts.services import active_template, send_for_signature, sign_contract


@pytest.fixture
def draft(db, employer, worker, norderstedt):
    def _make(ctype=ContractType.MINIJOB, hours="40", wage="15.00", start=date(2026, 10, 1)):
        return ContractDraft.objects.create(
            employer=employer, worker=worker, template=active_template(ctype),
            contract_type=ctype, start_date=start, hours_per_month=Decimal(hours),
            hourly_wage=Decimal(wage), workplace=norderstedt,
        )

    return _make


@pytest.mark.django_db
class TestCompliance:
    def test_pragurile_sunt_datate_nu_constante(self):
        assert WageFloor.current("GENERAL", date(2025, 6, 1)) == Decimal("12.82")
        assert WageFloor.current("GENERAL", date(2026, 6, 1)) == Decimal("13.90")
        assert MinijobThreshold.current(date(2025, 6, 1)) == Decimal("556.00")

    def test_tariful_de_ramura_creste_in_2026(self):
        """Tariful e allgemeinverbindlich (§ 7 AEntG): leagă toate firmele."""
        assert WageFloor.current("GEBAEUDE", date(2025, 6, 1)) == Decimal("14.25")
        assert WageFloor.current("GEBAEUDE", date(2026, 6, 1)) == Decimal("15.00")

    def test_severitatea_e_tipizata_nu_dedusa_din_text(self, draft):
        d = draft(ContractType.WERKVERTRAG, hours="60", wage="10.00")
        codes = {i.code: i.blocking for i in d.compliance_report()}
        # La un Dienstleistungsvertrag pragul avertizează; la un contract de muncă blochează.
        assert codes["WAGE_FLOOR"] is False
        assert codes["SCHEINSELBSTSTAENDIGKEIT"] is False
        employment = draft(ContractType.TEILZEIT, hours="80", wage="10.00")
        assert {i.code: i.blocking for i in employment.compliance_report()}["WAGE_FLOOR"] is True

    def test_40_ore_la_tariful_2026_ramane_minijob_valid(self, draft):
        """40 h × 15,00 € = 600 € — sub Geringfügigkeitsgrenze de 603 €. La limită."""
        d = draft(hours="40", wage="15.00")
        assert d.monthly_gross == Decimal("600.00")
        assert d.compliance_issues() == []

    def test_tariful_2026_impinge_minijobul_la_limita(self, draft):
        """41 de ore la tariful nou depășesc deja pragul — 40 h e maximul real."""
        d = draft(hours="41", wage="15.00")
        assert any("depășește pragul Minijob" in i for i in d.compliance_issues())

    def test_depasirea_pragului_minijob_e_semnalata(self, draft):
        d = draft(hours="45", wage="15.00")
        assert d.monthly_gross == Decimal("675.00")
        assert any("depășește pragul Minijob" in i for i in d.compliance_issues())

    def test_sub_mindestlohn_de_ramura_e_semnalat(self, draft):
        d = draft(ContractType.TEILZEIT, hours="80", wage="13.00")
        floor = WageFloor.current(WageFloor.Kind.GEBAEUDE, d.start_date)
        assert any("sub pragul" in i for i in d.compliance_issues())
        # Pragul se rezolvă la data de început, nu la o constantă din test.
        assert str(floor) in " ".join(d.compliance_issues())
        assert floor > WageFloor.current(WageFloor.Kind.GENERAL, d.start_date)

    def test_werkvertrag_avertizeaza_scheinselbststaendigkeit(self, draft):
        d = draft(ContractType.WERKVERTRAG, hours="60", wage="22.00")
        assert d.engagement_model == EngagementModel.INDEPENDENT
        assert any("Scheinselbst" in i for i in d.compliance_issues())

    def test_avertismentul_nu_blocheaza_trimiterea(self, draft):
        d = draft(ContractType.WERKVERTRAG, hours="60", wage="22.00")
        assert send_for_signature(d) == []
        d.refresh_from_db()
        assert d.status == DraftStatus.SENT

    def test_incalcarea_blocheaza_trimiterea(self, draft):
        d = draft(hours="45", wage="14.25")
        blocking = send_for_signature(d)
        assert blocking
        d.refresh_from_db()
        assert d.status == DraftStatus.DRAFT


@pytest.mark.django_db
class TestSignature:
    def test_textul_se_ingheata_la_trimitere(self, draft):
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        assert len(d.rendered_body) > 500
        assert len(d.body_sha256) == 64
        assert "Minijob-Zentrale" in d.rendered_body

    def test_sablonul_modificat_nu_rescrie_contractul_semnat(self, draft):
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        frozen = d.rendered_body
        d.template.body = "TEXT COMPLET NOU"
        d.template.save()
        d.refresh_from_db()
        assert d.rendered_body == frozen

    def test_ambele_parti_semneaza_acelasi_hash(self, draft, employer, worker):
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        sign_contract(d, employer, "Klaus Meyer")
        d.refresh_from_db()
        assert d.status == DraftStatus.SENT, "o singură semnătură nu închide contractul"
        sign_contract(d, worker, "Maria Ionescu")
        d.refresh_from_db()
        assert d.status == DraftStatus.SIGNED
        assert len({s.document_sha256 for s in d.signatures.all()}) == 1

    def test_un_tert_nu_poate_semna(self, draft, employer, worker, norderstedt):
        from apps.accounts.enums import Capability, EntityType
        from apps.accounts.models import User
        from apps.accounts.services import create_account

        outsider = create_account(
            user=User.objects.create_user("x@example.de", "parola-lunga-123"),
            entity_type=EntityType.COMPANY, display_name="Alt SRL",
            capabilities=[Capability.EMPLOYER], locality=norderstedt,
        )
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        with pytest.raises(ValueError):
            sign_contract(d, outsider, "Intrus")

    def test_semnatura_de_doua_ori_e_refuzata(self, draft, employer):
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        sign_contract(d, employer, "Klaus Meyer")
        with pytest.raises(ValueError):
            sign_contract(d, employer, "Klaus Meyer")

    def test_semnatura_e_imutabila(self, draft, employer):
        d = draft()
        send_for_signature(d)
        d.refresh_from_db()
        signature = sign_contract(d, employer, "Klaus Meyer")
        signature.signer_name = "Altcineva"
        with pytest.raises(RuntimeError):
            signature.save()
