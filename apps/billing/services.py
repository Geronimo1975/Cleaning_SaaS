"""
Logica de comenzi. Comanda se naște din cererea activată în marketplace —
un singur drum, folosit și de backfill — și își schimbă starea doar pe aici.
"""

from django.db import transaction
from django.utils import timezone

from .enums import ContractKind, DocumentType, OrderStatus
from .models import Customer, Order
from .numbering import allocate


class BillingError(ValueError):
    pass


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.ACTIVE: {OrderStatus.SUSPENDED, OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.SUSPENDED: {OrderStatus.ACTIVE, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


@transaction.atomic
def create_order_from_request(request, site, *, actor) -> Order:
    """
    Customer + Order pentru o cerere ACTIVĂ. Idempotent prin `source_offer`:
    a doua chemare întoarce comanda existentă, nu creează alta.
    """
    from apps.marketplace.models import RequestStatus

    offer = request.awarded_offer
    if request.status != RequestStatus.ACTIVE or offer is None:
        raise BillingError("Comanda se creează doar dintr-o cerere activată.")

    existing = Order.objects.filter(source_offer=offer).first()
    if existing is not None:
        return existing

    customer, _ = Customer.objects.get_or_create(provider=offer.provider, account=request.client)
    order = Order(
        provider=offer.provider,
        customer=customer,
        site=site,
        category=request.category,
        order_number=allocate(offer.provider, DocumentType.ORDER, offer.earliest_start.year),
        title=request.title[:200],
        start_date=offer.earliest_start,
        source_offer=offer,
    )
    order.full_clean()
    order.save()
    return order


def transition_order(order: Order, new_status: str, *, actor) -> Order:
    if actor.pk != order.provider_id:
        raise BillingError("Doar prestatorul își schimbă comenzile.")
    if new_status not in ALLOWED_TRANSITIONS[order.status]:
        raise BillingError(
            f"Din „{order.get_status_display()}” nu se poate trece la „{new_status}”."
        )
    fields = ["status"]
    order.status = new_status
    if (
        new_status == OrderStatus.COMPLETED
        and order.contract_kind == ContractKind.WERKVERTRAG
        and order.accepted_at is None
    ):
        order.accepted_at = timezone.now()   # Abnahme, §641 BGB
        fields.append("accepted_at")
    order.save(update_fields=fields)
    return order
