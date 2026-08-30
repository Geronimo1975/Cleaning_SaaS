"""
Guvernanța cooperativei.

Două reguli de model, amândouă cu consecințe juridice:

  1. Membru poate fi doar un Betrieb. Un Minijobber e angajatul cuiva; dacă ar
     putea fi „membru", cuvântul ar fi un eufemism pentru angajat și construcția
     ar cădea în §7 SGB IV.
  2. Regulile de repartizare se votează, deci sunt rânduri datate, nu constante
     în cod — altfel un vot al membrilor ar cere un deploy.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.enums import Capability, EntityType, LegalStatus
from apps.accounts.models import User
from apps.accounts.services import create_account
from apps.cooperative.models import (
    CooperativeMembership,
    DispatchPolicy,
    MembershipStatus,
    Resolution,
)
from apps.marketplace.scoring import DEFAULT_WEIGHTS, resolve_weights, score_offers
from apps.marketplace.services import publish_request


@pytest.fixture
def resolution(db):
    return Resolution.objects.create(
        reference="Beschluss 2026-03", title="Vergaberichtlinie 2026",
        adopted_on=date(2026, 3, 15),
    )


def _member(account, number="M-001", **kwargs):
    return CooperativeMembership(account=account, member_number=number, **kwargs)


@pytest.mark.django_db
class TestMembership:
    def test_o_firma_poate_fi_membru(self, employer):
        membership = _member(employer, status=MembershipStatus.ACTIVE)
        membership.full_clean()
        membership.save()
        assert membership.is_voting

    def test_un_independent_cu_gewerbe_poate_fi_membru(self, db, norderstedt):
        account = create_account(
            user=User.objects.create_user("selbst@example.de", "parola-lunga-123"),
            entity_type=EntityType.INDIVIDUAL, display_name="Anna Klein",
            capabilities=[Capability.WORKER], locality=norderstedt,
            legal_status=LegalStatus.SELBSTSTAENDIG,
        )
        _member(account).full_clean()

    def test_un_minijobber_nu_poate_fi_membru(self, worker):
        """Un Minijobber e angajatul cuiva, nu un Betrieb."""
        with pytest.raises(ValidationError, match="Betrieb"):
            _member(worker).full_clean()

    def test_un_cont_nedeclarat_nu_poate_fi_membru(self, worker):
        worker.legal_status = LegalStatus.UNDECLARED
        worker.save()
        with pytest.raises(ValidationError, match="Betrieb"):
            _member(worker).full_clean()

    def test_retragerea_nu_precede_aderarea(self, employer):
        membership = _member(
            employer, joined_on=date(2026, 3, 1), left_on=date(2026, 2, 1)
        )
        with pytest.raises(ValidationError):
            membership.full_clean()

    def test_nu_se_confunda_cu_accounts_membership(self, employer):
        """`accounts.Membership` leagă User↔Account. Concepte diferite."""
        from apps.accounts.models import Membership

        _member(employer, status=MembershipStatus.ACTIVE).save()
        assert Membership.objects.filter(account=employer).exists()
        assert employer.cooperative_membership.member_number == "M-001"


@pytest.mark.django_db
class TestDispatchPolicy:
    def test_ponderile_trebuie_sa_insumeze_unu(self, resolution):
        policy = DispatchPolicy(
            name="Greșită", valid_from=date(2026, 1, 1), adopted_by=resolution,
            weights={"price": "0.50", "verification": "0.25", "experience": "0.20",
                     "availability": "0.15", "proximity": "0.10"},
        )
        with pytest.raises(ValidationError, match="însumeze"):
            policy.full_clean()

    def test_criteriile_sunt_fixe(self, resolution):
        policy = DispatchPolicy(
            name="Inventată", valid_from=date(2026, 1, 1),
            weights={"price": "0.5", "simpatie": "0.5"},
        )
        with pytest.raises(ValidationError, match="Criteriile"):
            policy.full_clean()

    def test_politica_se_rezolva_la_data(self, resolution):
        DispatchPolicy.objects.create(
            name="2025", valid_from=date(2025, 1, 1), valid_to=date(2025, 12, 31),
            weights={"price": "0.50", "verification": "0.05", "experience": "0.20",
                     "availability": "0.15", "proximity": "0.10"},
        )
        curenta = DispatchPolicy.objects.create(
            name="2026", valid_from=date(2026, 1, 1), adopted_by=resolution,
            weights={"price": "0.20", "verification": "0.30", "experience": "0.20",
                     "availability": "0.15", "proximity": "0.15"},
        )
        assert DispatchPolicy.current(date(2025, 6, 1)).name == "2025"
        assert DispatchPolicy.current(date(2026, 6, 1)) == curenta

    def test_fara_politica_se_folosesc_valorile_implicite(self):
        assert resolve_weights(None) == DEFAULT_WEIGHTS


@pytest.mark.django_db
class TestPolicyAffectsRanking:
    def _two_offers(self, service_request, make_provider, make_offer):
        from apps.accounts.enums import VerificationLevel

        ieftin = make_provider("Ieftin", years=0, verification=VerificationLevel.NONE)
        bun = make_provider("Verificat", years=10, verification=VerificationLevel.DOCUMENTS)
        make_offer(service_request, ieftin, price="60", minutes=180)
        make_offer(service_request, bun, price="85", minutes=180)
        return ieftin, bun

    def test_votul_membrilor_schimba_clasamentul(
        self, service_request, make_provider, make_offer, resolution
    ):
        DispatchPolicy.objects.create(
            name="Prețul decide", valid_from=date(2026, 1, 1), adopted_by=resolution,
            weights={"price": "0.80", "verification": "0.05", "experience": "0.05",
                     "availability": "0.05", "proximity": "0.05"},
        )
        publish_request(service_request, invite=False)
        ieftin, bun = self._two_offers(service_request, make_provider, make_offer)
        assert score_offers(service_request)[0].offer.provider == ieftin

    def test_politica_fixata_la_publicare_nu_se_schimba_retroactiv(
        self, service_request, make_provider, make_offer, resolution
    ):
        """
        Prestatorul respins trebuie să poată reconstitui de ce a pierdut. Dacă
        un vot de mâine ar rescrie clasamentul de azi, explicația devine falsă.
        """
        pret_decide = DispatchPolicy.objects.create(
            name="Prețul decide", valid_from=date(2026, 1, 1), adopted_by=resolution,
            weights={"price": "0.80", "verification": "0.05", "experience": "0.05",
                     "availability": "0.05", "proximity": "0.05"},
        )
        publish_request(service_request, invite=False)
        service_request.refresh_from_db()
        assert service_request.dispatch_policy == pret_decide
        ieftin, bun = self._two_offers(service_request, make_provider, make_offer)

        # Membrii votează altceva mâine.
        pret_decide.valid_to = timezone.localdate()
        pret_decide.save()
        DispatchPolicy.objects.create(
            name="Calitatea decide", valid_from=timezone.localdate() + timedelta(days=1),
            weights={"price": "0.05", "verification": "0.45", "experience": "0.30",
                     "availability": "0.10", "proximity": "0.10"},
        )
        service_request.refresh_from_db()
        assert score_offers(service_request)[0].offer.provider == ieftin, (
            "cererea rămâne judecată după politica de la publicare"
        )

    def test_descompunerea_arata_ponderile_aplicate(
        self, service_request, make_provider, make_offer, resolution
    ):
        DispatchPolicy.objects.create(
            name="Prețul decide", valid_from=date(2026, 1, 1), adopted_by=resolution,
            weights={"price": "0.80", "verification": "0.05", "experience": "0.05",
                     "availability": "0.05", "proximity": "0.05"},
        )
        publish_request(service_request, invite=False)
        self._two_offers(service_request, make_provider, make_offer)
        explained = dict(
            (label, weight) for label, _, weight in score_offers(service_request)[0].explain()
        )
        assert explained["Preț pe oră"] == "pondere 80 %"
