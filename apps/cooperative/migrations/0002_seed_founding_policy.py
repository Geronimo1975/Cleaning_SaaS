"""
Politica de repartizare fondatoare, ca rând — nu ca dicționar în cod.

Ponderile sunt cele aflate în uz la momentul înființării. Din clipa în care
adunarea generală votează altele, se adaugă un rând nou cu `valid_from` și
hotărârea care l-a adoptat; nimeni nu editează cod pentru asta.
"""

from datetime import date

from django.db import migrations

WEIGHTS = {
    "price": "0.30",
    "verification": "0.25",
    "experience": "0.20",
    "availability": "0.15",
    "proximity": "0.10",
}


def forwards(apps, schema_editor):
    apps.get_model("cooperative", "DispatchPolicy").objects.update_or_create(
        name="Vergaberichtlinie – Gründungsfassung",
        defaults={
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
            "weights": WEIGHTS,
            "note": (
                "Ponderi de pornire, preluate din cod la introducerea politicilor "
                "votabile. Se înlocuiesc prin hotărâre a adunării generale."
            ),
        },
    )


def backwards(apps, schema_editor):
    apps.get_model("cooperative", "DispatchPolicy").objects.filter(
        name="Vergaberichtlinie – Gründungsfassung"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("cooperative", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
