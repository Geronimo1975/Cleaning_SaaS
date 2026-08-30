"""
Cele trei șabloane de contract cerute de unitate, plus varianta de prestator.

Textul e un SCHELET juridic corect structurat, nu un contract gata de semnat:
trebuie trecut o dată printr-un Fachanwalt für Arbeitsrecht înainte de prima
utilizare reală. Structura urmează §2 NachweisG (elementele obligatorii ale
raportului de muncă), care din 2025 pot fi comunicate în Textform.
"""

from django.db import migrations

COMMON_HEADER = """<h1>{{ title }}</h1>
<p><strong>zwischen</strong><br>
{{ employer.legal_name|default:employer.display_name }},
{{ employer.street }}, {{ employer.postal_code }} {{ employer.locality.name }}
&mdash; nachfolgend &bdquo;Arbeitgeber&ldquo; &mdash;</p>
<p><strong>und</strong><br>
{{ worker.display_name }}, {{ worker.street }},
{{ worker.postal_code }} {{ worker.locality.name }}
&mdash; nachfolgend &bdquo;Arbeitnehmer&ldquo; &mdash;</p>

<h2>&sect; 1 Beginn und Dauer</h2>
<p>Das Arbeitsverh&auml;ltnis beginnt am {{ draft.start_date }}.
{% if draft.end_date %}Es ist befristet bis zum {{ draft.end_date }}.
{% else %}Es wird auf unbestimmte Zeit geschlossen.{% endif %}
Die Probezeit betr&auml;gt {{ draft.probation_months }} Monate.</p>

<h2>&sect; 2 T&auml;tigkeit und Arbeitsort</h2>
<p>Der Arbeitnehmer wird als Reinigungskraft besch&auml;ftigt.
Arbeitsort ist {{ workplace.name }}.</p>
"""

COMMON_FOOTER = """
<h2>&sect; 5 Urlaub</h2>
<p>Der Urlaubsanspruch betr&auml;gt {{ draft.vacation_days }} Arbeitstage pro Kalenderjahr
(mindestens der gesetzliche Anspruch nach &sect; 3 BUrlG).</p>

<h2>&sect; 6 K&uuml;ndigung</h2>
<p>Es gelten die gesetzlichen K&uuml;ndigungsfristen nach &sect; 622 BGB.
W&auml;hrend der Probezeit betr&auml;gt die Frist zwei Wochen.</p>

<h2>&sect; 7 Nebenabreden</h2>
<p>&Auml;nderungen und Erg&auml;nzungen bed&uuml;rfen der Textform (&sect; 126b BGB).</p>
"""

TEMPLATES = [
    ("VOLLZEIT", "Arbeitsvertrag – Vollzeit", COMMON_HEADER + """
<h2>&sect; 3 Arbeitszeit</h2>
<p>Die regelm&auml;&szlig;ige monatliche Arbeitszeit betr&auml;gt
{{ draft.hours_per_month }} Stunden.</p>

<h2>&sect; 4 Verg&uuml;tung</h2>
<p>Der Stundenlohn betr&auml;gt {{ draft.hourly_wage }} &euro; brutto,
das monatliche Bruttoentgelt somit {{ monthly_gross }} &euro;.
Die Zahlung erfolgt bargeldlos zum Monatsende.</p>
""" + COMMON_FOOTER),

    ("TEILZEIT", "Arbeitsvertrag – Teilzeit", COMMON_HEADER + """
<h2>&sect; 3 Arbeitszeit</h2>
<p>Es handelt sich um ein Teilzeitarbeitsverh&auml;ltnis mit
{{ draft.hours_per_month }} Stunden monatlich. Lage und Verteilung werden
einvernehmlich festgelegt. Der Arbeitnehmer darf gegen&uuml;ber vergleichbaren
Vollzeitbesch&auml;ftigten nicht benachteiligt werden (&sect; 4 TzBfG).</p>

<h2>&sect; 4 Verg&uuml;tung</h2>
<p>Der Stundenlohn betr&auml;gt {{ draft.hourly_wage }} &euro; brutto,
das monatliche Bruttoentgelt somit {{ monthly_gross }} &euro;.</p>
""" + COMMON_FOOTER),

    ("MINIJOB", "Arbeitsvertrag – geringfügige Beschäftigung (Minijob)",
     COMMON_HEADER + """
<h2>&sect; 3 Arbeitszeit</h2>
<p>Die monatliche Arbeitszeit betr&auml;gt {{ draft.hours_per_month }} Stunden.</p>

<h2>&sect; 4 Verg&uuml;tung und Status</h2>
<p>Der Stundenlohn betr&auml;gt {{ draft.hourly_wage }} &euro;, das monatliche
Bruttoentgelt {{ monthly_gross }} &euro;. Das Arbeitsverh&auml;ltnis ist als
geringf&uuml;gige Besch&auml;ftigung nach &sect; 8 Abs. 1 Nr. 1 SGB IV angelegt.
Der Arbeitgeber meldet die Besch&auml;ftigung bei der Minijob-Zentrale an.
Der Arbeitnehmer versichert, dass die Geringf&uuml;gigkeitsgrenze unter
Ber&uuml;cksichtigung weiterer Besch&auml;ftigungen nicht &uuml;berschritten wird.</p>
<p>Der Arbeitnehmer ist rentenversicherungspflichtig und kann sich auf Antrag
befreien lassen (&sect; 6 Abs. 1b SGB VI).</p>
""" + COMMON_FOOTER),

    ("WERKVERTRAG", "Dienstleistungsvertrag – selbständige Reinigungskraft", """
<h1>{{ title }}</h1>
<p><strong>zwischen</strong> {{ employer.legal_name|default:employer.display_name }}
&mdash; &bdquo;Auftraggeber&ldquo; &mdash; <strong>und</strong>
{{ worker.display_name }} &mdash; &bdquo;Auftragnehmer&ldquo; &mdash;</p>

<h2>&sect; 1 Gegenstand</h2>
<p>Der Auftragnehmer erbringt Reinigungsleistungen in {{ workplace.name }}
ab {{ draft.start_date }} als selbst&auml;ndiger Unternehmer.</p>

<h2>&sect; 2 Selbst&auml;ndigkeit</h2>
<p>Der Auftragnehmer ist nicht weisungsgebunden, bestimmt Arbeitszeit und
Arbeitsweise selbst, ist nicht in die Betriebsorganisation eingegliedert und
ist f&uuml;r weitere Auftraggeber t&auml;tig. Er tr&auml;gt selbst Sorge f&uuml;r
Steuern, Sozialversicherung und Gewerbeanmeldung.</p>

<h2>&sect; 3 Verg&uuml;tung</h2>
<p>Das Honorar betr&auml;gt {{ draft.hourly_wage }} &euro; je Stunde zzgl. USt.
Die Abrechnung erfolgt monatlich per Rechnung.</p>
"""),
]


def forwards(apps, schema_editor):
    ContractTemplate = apps.get_model("contracts", "ContractTemplate")
    for ctype, title, body in TEMPLATES:
        ContractTemplate.objects.update_or_create(
            contract_type=ctype, version="1.0", language="de",
            defaults={"title": title, "body": "{% load i18n %}" + body, "is_active": True},
        )


def backwards(apps, schema_editor):
    apps.get_model("contracts", "ContractTemplate").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("contracts", "0002_seed_wage_floors")]
    operations = [migrations.RunPython(forwards, backwards)]
