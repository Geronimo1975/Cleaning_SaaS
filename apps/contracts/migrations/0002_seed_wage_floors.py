"""
Praguri salariale de pornire.

ATENȚIE: valorile de mai jos trebuie CONFIRMATE înainte de a genera contracte
reale. Mindestlohn-ul general și pragul Minijob sunt publicate anual; cel de
ramură (Gebäudereinigung) rezultă din Tarifvertrag și e allgemeinverbindlich
doar cât timp declarația e în vigoare. De aceea sunt rânduri cu `valid_from`,
nu constante — se corectează din admin, fără deploy.
"""

from datetime import date

from django.db import migrations

GENERAL = [
    (date(2025, 1, 1), date(2025, 12, 31), "12.82", "MiLoG 2025"),
    (date(2026, 1, 1), None, "13.90", "MiLoG 2026 — DE CONFIRMAT"),
]
GEBAEUDE = [
    (date(2025, 1, 1), None, "14.25", "Gebäudereinigung LG1 Innenreinigung — DE CONFIRMAT"),
]
MINIJOB = [
    (date(2025, 1, 1), date(2025, 12, 31), "556.00", "Geringfügigkeitsgrenze 2025"),
    (date(2026, 1, 1), None, "603.00", "Mindestlohn × 130/3 — DE CONFIRMAT"),
]


def forwards(apps, schema_editor):
    WageFloor = apps.get_model("contracts", "WageFloor")
    MinijobThreshold = apps.get_model("contracts", "MinijobThreshold")
    for kind, rows in (("GENERAL", GENERAL), ("GEBAEUDE", GEBAEUDE)):
        for vf, vt, amount, note in rows:
            WageFloor.objects.update_or_create(
                kind=kind, valid_from=vf,
                defaults={"valid_to": vt, "hourly_amount": amount, "source_note": note},
            )
    for vf, vt, limit, note in MINIJOB:
        MinijobThreshold.objects.update_or_create(
            valid_from=vf,
            defaults={"valid_to": vt, "monthly_limit": limit, "source_note": note},
        )


def backwards(apps, schema_editor):
    apps.get_model("contracts", "WageFloor").objects.all().delete()
    apps.get_model("contracts", "MinijobThreshold").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("contracts", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
