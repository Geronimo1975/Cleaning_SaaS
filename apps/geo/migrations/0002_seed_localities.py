"""
Localitățile de lansare: inelul nordic al Hamburgului.

Listă închisă, populată prin data migration — text liber distruge și filtrarea,
și SEO-ul pe „Reinigungskraft {oraș}". Slug-urile sunt definitive.

Val 1 (`is_active=True`) = zona de lansare efectivă. Restul se activează din
admin, fără deploy, când apar prestatori acolo.

Coordonatele rămân goale intenționat: se completează prin geocodare, nu ghicite.
Matching-ul pe distanță (v2) depinde de ele.
"""

from django.db import migrations

REGIONS = [
    ("Schleswig-Holstein", "schleswig-holstein", "SH"),
    ("Hamburg", "hamburg", "HH"),
]

# (region_code, nume, slug, PLZ, activ_val_1, ordine)
LOCALITIES = [
    # --- Val 1: inelul nordic imediat ---------------------------------
    ("SH", "Norderstedt", "norderstedt", "22846", True, 10),
    ("SH", "Henstedt-Ulzburg", "henstedt-ulzburg", "24558", True, 11),
    ("SH", "Quickborn", "quickborn", "25451", True, 12),
    ("SH", "Pinneberg", "pinneberg", "25421", True, 13),
    ("SH", "Ahrensburg", "ahrensburg", "22926", True, 14),
    ("SH", "Kaltenkirchen", "kaltenkirchen", "24568", True, 15),
    ("SH", "Bad Segeberg", "bad-segeberg", "23795", True, 16),
    ("SH", "Elmshorn", "elmshorn", "25335", True, 17),
    ("SH", "Wedel", "wedel", "22880", True, 18),
    ("SH", "Bargteheide", "bargteheide", "22941", True, 19),
    ("SH", "Rellingen", "rellingen", "25462", True, 20),
    ("SH", "Halstenbek", "halstenbek", "25469", True, 21),
    ("SH", "Schenefeld", "schenefeld", "22869", True, 22),
    # districtele hamburgheze dinspre nord
    ("HH", "Hamburg-Nord", "hamburg-nord", "22299", True, 30),
    ("HH", "Eimsbüttel", "hamburg-eimsbuettel", "20255", True, 31),
    ("HH", "Wandsbek", "hamburg-wandsbek", "22041", True, 32),
    ("HH", "Altona", "hamburg-altona", "22765", True, 33),
    # --- Val 2: se activează la nevoie --------------------------------
    ("SH", "Bad Bramstedt", "bad-bramstedt", "24576", False, 50),
    ("SH", "Bad Oldesloe", "bad-oldesloe", "23843", False, 51),
    ("SH", "Barmstedt", "barmstedt", "25355", False, 52),
    ("SH", "Tornesch", "tornesch", "25436", False, 53),
    ("SH", "Uetersen", "uetersen", "25436", False, 54),
    ("SH", "Reinbek", "reinbek", "21465", False, 55),
    ("SH", "Glinde", "glinde", "21509", False, 56),
    ("SH", "Trittau", "trittau", "22946", False, 57),
    ("SH", "Itzehoe", "itzehoe", "25524", False, 58),
    ("SH", "Neumünster", "neumuenster", "24534", False, 59),
    ("HH", "Hamburg-Mitte", "hamburg-mitte", "20095", False, 60),
    ("HH", "Bergedorf", "hamburg-bergedorf", "21029", False, 61),
    ("HH", "Harburg", "hamburg-harburg", "21073", False, 62),
]


def forwards(apps, schema_editor):
    Region = apps.get_model("geo", "Region")
    Locality = apps.get_model("geo", "Locality")

    regions = {}
    for name, slug, code in REGIONS:
        regions[code], _ = Region.objects.get_or_create(
            code=code, defaults={"name": name, "slug": slug}
        )

    for code, name, slug, plz, active, order in LOCALITIES:
        Locality.objects.update_or_create(
            slug=slug,
            defaults={
                "region": regions[code],
                "name": name,
                "postal_code": plz,
                "is_active": active,
                "sort_order": order,
            },
        )


def backwards(apps, schema_editor):
    apps.get_model("geo", "Locality").objects.filter(
        slug__in=[row[2] for row in LOCALITIES]
    ).delete()
    apps.get_model("geo", "Region").objects.filter(
        code__in=[r[2] for r in REGIONS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("geo", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
