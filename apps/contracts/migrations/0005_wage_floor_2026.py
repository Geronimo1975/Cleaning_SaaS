"""
Tariflohn LG 1 ab 01.01.2026: 15,00 €/h.

Zeila GEBAEUDE semănată inițial (14,25 € de la 2025-01-01, `valid_to=None`) rămânea
valabilă la infinit. Un contract cu început în 2026 trecea verificarea la 14,25 €
și încălca totuși Mindestlohntarifvertrag-ul, care e allgemeinverbindlich prin
Rechtsverordnung nach § 7 AEntG din 28.01.2025 — deci leagă TOATE firmele de
curățenie, indiferent de apartenența la un tarif.

Sursă: https://pland.app/blog/tariflohn-2026-in-der-gebaudereinigung-das-sind-die-neuen-stundenlohne-ab-1-januar-2026
"""

from datetime import date

from django.db import migrations


def forwards(apps, schema_editor):
    WageFloor = apps.get_model("contracts", "WageFloor")

    WageFloor.objects.filter(
        kind="GEBAEUDE", valid_from=date(2025, 1, 1)
    ).update(
        valid_to=date(2025, 12, 31),
        source_note="Gebäudereinigung LG1 Innenreinigung, Mindestlohntarifvertrag 2025",
    )
    WageFloor.objects.update_or_create(
        kind="GEBAEUDE", valid_from=date(2026, 1, 1),
        defaults={
            "valid_to": None,
            "hourly_amount": "15.00",
            "source_note": "Lohntarifvertrag LG 1, ab 01.01.2026, allgemeinverbindlich (§ 7 AEntG)",
        },
    )


def backwards(apps, schema_editor):
    WageFloor = apps.get_model("contracts", "WageFloor")
    WageFloor.objects.filter(kind="GEBAEUDE", valid_from=date(2026, 1, 1)).delete()
    WageFloor.objects.filter(kind="GEBAEUDE", valid_from=date(2025, 1, 1)).update(valid_to=None)


class Migration(migrations.Migration):
    dependencies = [("contracts", "0004_fix_template_titles")]
    operations = [migrations.RunPython(forwards, backwards)]
