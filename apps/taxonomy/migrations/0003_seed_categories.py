"""
Taxonomia de servicii, în germană.

Două niveluri, 24 de frunze. Doar frunzele sunt selectabile. Vocabular comun
între profil, anunț și — în v2 — cererea de serviciu.

`name` = eticheta internă (RO, pentru admin), `name_de` = ce vede publicul.
`is_35a_eligible` marchează serviciile pe care clientul privat le deduce 20%
din impozit (§35a EStG) — doar prestații executate în gospodăria clientului.
"""

from django.db import migrations

# (slug, name_ro, name_de, is_35a, ordine)
TREE = [
    ("wohnungsreinigung", "Curățenie rezidențială", "Wohnungsreinigung", 10, [
        ("wohnungs-und-hausreinigung", "Curățenie apartament / casă",
         "Wohnungs- und Hausreinigung", True, 10),
        ("unterhaltsreinigung-privat", "Curățenie periodică (abonament)",
         "Regelmäßige Unterhaltsreinigung", True, 20),
        ("grundreinigung", "Curățenie de profunzime", "Grundreinigung", True, 30),
        ("umzugsreinigung", "Curățenie după mutare / predare",
         "Umzugs- und Endreinigung", True, 40),
        ("polsterreinigung", "Curățare canapele, saltele, tapițerie",
         "Polster- und Matratzenreinigung", True, 50),
        ("fensterreinigung-privat", "Spălare geamuri — rezidențial",
         "Fensterreinigung (privat)", True, 60),
    ]),
    ("gewerbereinigung", "Curățenie comercială", "Gewerbereinigung", 20, [
        ("bueroreinigung", "Curățenie birouri", "Büroreinigung", False, 10),
        ("ladenreinigung", "Curățenie spații comerciale / retail",
         "Laden- und Einzelhandelsreinigung", False, 20),
        ("gastronomiereinigung", "Curățenie HoReCa",
         "Hotel- und Gastronomiereinigung", False, 30),
        ("praxisreinigung", "Curățenie spații medicale",
         "Praxis- und Medizinreinigung", False, 40),
        ("treppenhausreinigung", "Curățenie scări de bloc și spații comune",
         "Treppenhaus- und Gemeinschaftsflächenreinigung", True, 50),
        ("industriereinigung", "Curățenie hale și spații industriale",
         "Hallen- und Industriereinigung", False, 60),
    ]),
    ("spezialreinigung", "Curățenie specializată", "Spezialreinigung", 30, [
        ("bauendreinigung", "Curățenie post-construcție / post-renovare",
         "Bauendreinigung", True, 10),
        ("glasreinigung-hoehe", "Spălare geamuri la înălțime",
         "Glasreinigung in Höhe / Höhenarbeit", False, 20),
        ("fassadenreinigung", "Curățare fațade și pavaje cu presiune",
         "Fassaden- und Pflasterreinigung", True, 30),
        ("schaedlingsbekaempfung", "Dezinfecție, dezinsecție, deratizare",
         "Desinfektion und Schädlingsbekämpfung", False, 40),
        ("teppichreinigung", "Curățare covoare și mochete — industrial",
         "Teppich- und Bodenreinigung", True, 50),
        ("lueftungsreinigung", "Curățare tubulatură ventilație și hote",
         "Lüftungs- und Dunstabzugsreinigung", False, 60),
        ("fahrzeugaufbereitung", "Curățenie interior auto",
         "Fahrzeuginnenreinigung", False, 70),
    ]),
    ("haushaltsnahe-dienstleistungen", "Servicii conexe",
     "Haushaltsnahe Dienstleistungen", 40, [
        ("haushaltshilfe", "Menaj la domiciliu (recurent)",
         "Haushaltshilfe (regelmäßig)", True, 10),
        ("waeschepflege", "Călcat și spălat rufe",
         "Wäsche waschen und bügeln", True, 20),
        ("gartenpflege", "Îngrijire spații verzi și curte",
         "Gartenpflege", True, 30),
        ("winterdienst", "Deszăpezire", "Winterdienst", True, 40),
        ("entruempelung", "Evacuare moloz și debarasare",
         "Entrümpelung und Entsorgung", True, 50),
    ]),
]


def forwards(apps, schema_editor):
    ServiceCategory = apps.get_model("taxonomy", "ServiceCategory")
    for slug, name, name_de, order, children in TREE:
        parent, _ = ServiceCategory.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "name_de": name_de, "sort_order": order,
                      "parent": None, "is_active": True},
        )
        for c_slug, c_name, c_name_de, deductible, c_order in children:
            ServiceCategory.objects.update_or_create(
                slug=c_slug,
                defaults={"parent": parent, "name": c_name, "name_de": c_name_de,
                          "sort_order": c_order, "is_active": True,
                          "is_35a_eligible": deductible},
            )


def backwards(apps, schema_editor):
    ServiceCategory = apps.get_model("taxonomy", "ServiceCategory")
    slugs = [c[0] for _, _, _, _, ch in TREE for c in ch] + [t[0] for t in TREE]
    ServiceCategory.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0002_servicecategory_is_35a_eligible")]
    operations = [migrations.RunPython(forwards, backwards)]
