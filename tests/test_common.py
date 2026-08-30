"""
TimeStampedModel.

Testul care contează nu e „câmpurile există", ci că baza abstractă a fost
aplicată SELECTIV. Un `updated_at` pe un jurnal append-only e o contradicție:
rândul refuză orice update prin `save()`, dar câmpul spune că se actualizează.
"""

import pytest
from django.apps import apps as django_apps

from apps.common.models import TimeStampedModel

# Jurnale, tabele de legătură și modele cu propriul ceas — vezi nota din
# apps/common/models.py. Dacă cineva le adaugă la TimeStampedModel, aici pică.
NEVER_TIMESTAMPED = [
    ("accounts", "ConsentRecord"),
    ("planning", "ShiftEvent"),
    ("contracts", "ContractSignature"),
    ("jobs", "IndexingTask"),
    ("accounts", "AccountService"),
    ("accounts", "ServiceArea"),
    ("devices", "TelemetrySession"),
]

TIMESTAMPED = [
    ("planning", "Site"),
    ("planning", "Zone"),
    ("planning", "Shift"),
    ("accounts", "WorkerProfile"),
    ("accounts", "CompanyProfile"),
    ("contracts", "WageFloor"),
    ("contracts", "MinijobThreshold"),
    ("geo", "Locality"),
    ("taxonomy", "ServiceCategory"),
    ("catalog", "ProductCategory"),
]


@pytest.mark.parametrize("app_label,model_name", TIMESTAMPED)
def test_modelele_mutabile_au_timestamps(app_label, model_name):
    model = django_apps.get_model(app_label, model_name)
    assert issubclass(model, TimeStampedModel)
    names = {f.name for f in model._meta.fields}
    assert {"created_at", "updated_at"} <= names


@pytest.mark.parametrize("app_label,model_name", NEVER_TIMESTAMPED)
def test_jurnalele_si_legaturile_nu_primesc_updated_at(app_label, model_name):
    model = django_apps.get_model(app_label, model_name)
    assert not issubclass(model, TimeStampedModel)
    assert "updated_at" not in {f.name for f in model._meta.fields}


@pytest.mark.django_db
def test_updated_at_se_misca_la_salvare(norderstedt):
    initial = norderstedt.updated_at
    norderstedt.sort_order = 99
    norderstedt.save(update_fields=["sort_order", "updated_at"])
    norderstedt.refresh_from_db()
    assert norderstedt.updated_at > initial


@pytest.mark.django_db
def test_created_at_nu_se_misca(norderstedt):
    created = norderstedt.created_at
    norderstedt.sort_order = 42
    norderstedt.save()
    norderstedt.refresh_from_db()
    assert norderstedt.created_at == created


@pytest.mark.django_db
def test_pragul_salarial_retine_cand_a_fost_modificat(db):
    """
    Motivul concret pentru care WageFloor a primit timestamps: de la commit-ul
    cu adminul, pragurile se editează din interfață. „Cine a schimbat
    Mindestlohn-ul și când" e o întrebare care se pune.
    """
    from apps.contracts.models import WageFloor

    floor = WageFloor.objects.filter(kind=WageFloor.Kind.GENERAL).first()
    assert floor is not None, "seed-ul de praguri există"
    before = floor.updated_at
    floor.source_note = "actualizat manual"
    floor.save()
    floor.refresh_from_db()
    assert floor.updated_at > before
