"""Politica de vizibilitate. Cel mai ușor de spart la o refactorizare."""

import pytest

from apps.accounts.visibility import AccountView, Relation
from apps.contracts.models import DraftStatus
from apps.jobs.models import Application


@pytest.mark.django_db
class TestVisibility:
    def test_anonim_nu_vede_contactul_unei_persoane(self, worker):
        v = AccountView(worker)
        assert v.relation == Relation.ANONYMOUS
        assert v.display_name == "Maria Ionescu"
        assert v.phone is None
        assert v.street is None

    def test_datele_de_firma_sunt_publice(self, employer):
        v = AccountView(employer)
        assert v.legal_name == "Seniorenresidenz Nord GmbH"

    def test_persoana_fizica_nu_expune_campuri_de_firma(self, worker):
        worker.legal_name = "nu ar trebui să existe"
        v = AccountView(worker, viewer_account=worker)
        assert v.legal_name is None, "câmpurile de firmă sunt ascunse pentru persoane fizice"

    def test_alt_cont_logat_nu_vede_contactul(self, worker, employer):
        v = AccountView(worker, viewer_account=employer)
        assert v.relation == Relation.AUTHENTICATED
        assert v.phone is None

    def test_candidatura_ridica_relatia_la_engaged(self, worker, employer, job):
        Application.objects.create(job=job, applicant_account=worker)
        v = AccountView(worker, viewer_account=employer)
        assert v.relation == Relation.ENGAGED
        assert v.phone == "+49 170 9998877"

    def test_statutul_fiscal_ramane_privat_chiar_si_engaged(self, worker, employer, job):
        Application.objects.create(job=job, applicant_account=worker)
        v = AccountView(worker, viewer_account=employer)
        assert v.legal_status is None, "statutul fiscal nu se expune altui cont"
        assert AccountView(worker, viewer_account=worker).legal_status == "MINIJOB"

    def test_contractul_semnat_ridica_relatia_la_engaged(
        self, worker, employer, signed_contract
    ):
        """Invitat direct, fără să fi aplicat vreodată la un anunț."""
        signed_contract()
        v = AccountView(employer, viewer_account=worker)
        assert v.relation == Relation.ENGAGED
        assert v.street == "Ulzburger Str. 40"

    def test_contractul_in_ciorna_nu_ridica_relatia(self, worker, employer, signed_contract):
        draft = signed_contract()
        draft.status = DraftStatus.DRAFT
        draft.save(update_fields=["status"])
        v = AccountView(employer, viewer_account=worker)
        assert v.relation == Relation.AUTHENTICATED, "o ciornă nu e încă o relație"
        assert v.street is None

    def test_staff_vede_tot(self, worker, employer):
        employer.user.is_staff = True
        v = AccountView(worker, user=employer.user)
        assert v.relation == Relation.STAFF
        assert v.legal_status == "MINIJOB"
