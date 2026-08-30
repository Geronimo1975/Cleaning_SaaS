"""
Baze abstracte partajate.

`TimeStampedModel` se aplică DELIBERAT selectiv, nu peste tot. Din cele 41 de
modele ale proiectului, trei categorii nu au ce căuta aici:

  Jurnale append-only — `ConsentRecord`, `ShiftEvent`, `IndexingTask`,
    `ContractSignature`. Au `created_at` (sau `signed_at`) și refuză orice
    update prin `save()`. Un `updated_at` pe un rând care nu se actualizează
    niciodată nu e informație în plus, e o invitație să fie modificat.

  Tabele de legătură — `AccountService`, `ServiceArea`, `TourStop`. Se creează
    și se șterg, nu se editează. Momentul modificării nu există.

  Modele cu propriul ceas — `TelemetrySession` (`started_at`/`ended_at`),
    `User` (`date_joined`/`last_login`). Un al doilea set de timpi ar pune
    întrebarea „care e cel adevărat".

Rămân entitățile care chiar se editează în timp și pentru care „când s-a
schimbat ultima dată" e o întrebare pe care o pune cineva: obiective, zone,
ture, profiluri, praguri salariale.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """Adaugă `created_at` / `updated_at`. Nu schimbă nimic altceva."""

    created_at = models.DateTimeField("Creat", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Actualizat", auto_now=True)

    class Meta:
        abstract = True
