"""
Numere de document fără goluri. Se alocă DOAR în tranzacția care creează
documentul, sub `select_for_update` — niciodată din `pk`, niciodată reutilizate.
Lock-ul pe rând ține pe Postgres; SQLite (doar local) serializează oricum.
"""

from django.db import transaction

from .models import DocumentSequence


@transaction.atomic
def allocate(provider, document_type: str, year: int) -> str:
    seq, _ = DocumentSequence.objects.select_for_update().get_or_create(
        provider=provider, document_type=document_type, year=year
    )
    number = f"{seq.prefix}-{year}-{seq.next_number:04d}"
    seq.next_number += 1
    seq.save(update_fields=["next_number"])
    return number
