"""
Backfill: cererile ACTIVE de dinaintea modulului de comenzi primesc Customer +
Order, cu aceeași cheie de obiectiv pe care o folosește activarea
(`Site(account=offer.provider, name=request.title[:160])`).

Lucrează pe modelele istorice primite de la migrație, deci nu importă
`services.py`. Migrațiile rulează serial — nu e nevoie de `select_for_update`.
"""


def backfill_orders(apps) -> int:
    ServiceRequest = apps.get_model("marketplace", "ServiceRequest")
    Site = apps.get_model("planning", "Site")
    Customer = apps.get_model("billing", "Customer")
    Order = apps.get_model("billing", "Order")
    DocumentSequence = apps.get_model("billing", "DocumentSequence")

    created = 0
    requests = (
        ServiceRequest.objects.filter(status="ACTIVE", awarded_offer__isnull=False)
        .select_related("awarded_offer", "client", "category")
        .order_by("pk")
    )
    for request in requests:
        offer = request.awarded_offer
        if Order.objects.filter(source_offer=offer).exists():
            continue
        site = Site.objects.filter(account_id=offer.provider_id, name=request.title[:160]).first()
        if site is None:
            continue
        customer, _ = Customer.objects.get_or_create(
            provider_id=offer.provider_id, account_id=request.client_id
        )
        year = offer.earliest_start.year
        seq, _ = DocumentSequence.objects.get_or_create(
            provider_id=offer.provider_id, document_type="ORDER", year=year
        )
        number = f"{seq.prefix}-{year}-{seq.next_number:04d}"
        seq.next_number += 1
        seq.save(update_fields=["next_number"])
        Order.objects.create(
            provider_id=offer.provider_id,
            customer=customer,
            site=site,
            category_id=request.category_id,
            order_number=number,
            title=request.title[:200],
            start_date=offer.earliest_start,
            source_offer=offer,
        )
        created += 1
    return created
