"""
Generatorul de plan săptămânal.

Nu e un optimizator matematic — e un repartizor lacom cu constrângeri tari.
Diferența contează: un optimizator care „aproape" respectă plafonul de ore
produce o încălcare legală. Aici, dacă o vizită nu încape fără să spargă o
regulă, rămâne NEALOCATĂ și apare în raport cu motivul.

Constrângeri tari:
  1. Bugetul de ore din contractul semnat (plafon legal, nu preferință)
  2. Max. 8 h pe zi de lucrător           — §3 ArbZG
  3. Min. 11 h odihnă între ture          — §5 ArbZG
  4. Duminica liberă                      — §9 ArbZG
  5. Lucrătorul deservește localitatea obiectivului
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction

from apps.contracts.models import ContractDraft, DraftStatus

from .models import PlanStatus, Shift, ShiftPlan, Zone

MAX_DAILY_MINUTES = 480          # §3 ArbZG: 8 h; 10 h doar cu compensare în 6 luni
MIN_REST_MINUTES = 11 * 60       # §5 ArbZG
SUNDAY = 7                       # §9 ArbZG
DAY_START = time(7, 0)
WEEKS_PER_MONTH = Decimal("52") / Decimal("12")


@dataclass
class WorkerCapacity:
    """Bugetul săptămânal al unui lucrător, derivat din contractul semnat."""

    account_id: int
    name: str
    weekly_minutes: int
    localities: set[int]
    used_minutes: int = 0
    per_day: dict[date, int] = field(default_factory=dict)
    day_end: dict[date, datetime] = field(default_factory=dict)

    @property
    def remaining(self) -> int:
        return self.weekly_minutes - self.used_minutes


def build_capacities(account, week_start: date) -> list[WorkerCapacity]:
    """
    Capacitatea vine EXCLUSIV din contracte semnate și active în săptămâna dată.
    Fără contract semnat, un om nu poate fi planificat — planificarea nu e
    locul unde se creează raporturi de muncă.
    """
    week_end = week_start + timedelta(days=6)
    contracts = (
        ContractDraft.objects.filter(
            employer=account, status=DraftStatus.SIGNED, start_date__lte=week_end
        )
        .exclude(end_date__lt=week_start)
        .select_related("worker")
    )
    capacities = []
    for contract in contracts:
        weekly = int(Decimal(contract.hours_per_month) * 60 / WEEKS_PER_MONTH)
        localities = set(
            contract.worker.areas.values_list("locality_id", flat=True)
        ) or {contract.workplace_id}
        capacities.append(
            WorkerCapacity(
                account_id=contract.worker_id,
                name=contract.worker.display_name,
                weekly_minutes=weekly,
                localities=localities,
            )
        )
    return capacities


def _fits(cap: WorkerCapacity, day: date, minutes: int, locality_ids) -> str | None:
    """Returnează motivul refuzului, sau None dacă tura încape."""
    if isinstance(locality_ids, int):
        locality_ids = {locality_ids}
    missing = set(locality_ids) - cap.localities
    if missing:
        return "nu deservește localitatea"
    if cap.remaining < minutes:
        return f"buget săptămânal epuizat ({cap.weekly_minutes} min contractate)"
    if cap.per_day.get(day, 0) + minutes > MAX_DAILY_MINUTES:
        return "ar depăși 8 h într-o zi (§3 ArbZG)"
    previous_end = cap.day_end.get(day - timedelta(days=1))
    if previous_end:
        start = datetime.combine(day, DAY_START)
        if (start - previous_end).total_seconds() / 60 < MIN_REST_MINUTES:
            return "sub 11 h de odihnă față de tura anterioară (§5 ArbZG)"
    return None


@transaction.atomic
def generate_week_plan(account, week_start: date, replace: bool = False) -> ShiftPlan:
    if week_start.isoweekday() != 1:
        raise ValueError("Săptămâna începe luni.")

    plan, created = ShiftPlan.objects.get_or_create(account=account, week_start=week_start)
    if not created:
        # Un plan publicat nu se rescrie: oamenii și-au organizat deja săptămâna
        # după el. Republicarea e o decizie explicită, nu un efect secundar.
        if plan.status == PlanStatus.PUBLISHED and not replace:
            raise ValueError("Planul e publicat. Regenerarea cere confirmare explicită.")
        plan.shifts.all().delete()

    capacities = build_capacities(account, week_start)
    zones = (
        Zone.objects.filter(site__account=account, is_active=True, site__is_active=True)
        .select_related("site", "category")
        .order_by("-minutes_per_visit")  # sarcinile grele întâi: încap mai greu
    )

    unmet: list[dict] = []
    shifts: list[Shift] = []

    # Rundele se așază primele: sunt blocuri indivizibile și mari, deci încap
    # cel mai greu. Zonele lor ies din bucla de mai jos.
    toured_zone_ids = _place_tours(account, week_start, plan, capacities, shifts, unmet)
    zones = [z for z in zones if z.pk not in toured_zone_ids]

    for zone in zones:
        days = _visit_days(zone, week_start)
        for visit_index, day in enumerate(days, start=1):
            reasons: dict[str, str] = {}
            candidate = None
            for cap in sorted(capacities, key=lambda c: -c.remaining):
                reason = _fits(cap, day, zone.minutes_per_visit, zone.site.locality_id)
                if reason is None:
                    candidate = cap
                    break
                reasons[cap.name] = reason

            if candidate is None:
                unmet.append({
                    "zone": zone.name,
                    "site": zone.site.name,
                    "date": day.isoformat(),
                    "minutes": zone.minutes_per_visit,
                    "reasons": reasons or {"—": "niciun lucrător cu contract semnat"},
                })
                continue

            start_minutes = candidate.per_day.get(day, 0)
            start = (datetime.combine(day, DAY_START) + timedelta(minutes=start_minutes))
            shifts.append(Shift(
                plan=plan, zone=zone, worker_id=candidate.account_id, date=day,
                start_time=start.time(), duration_minutes=zone.minutes_per_visit,
            ))
            candidate.used_minutes += zone.minutes_per_visit
            candidate.per_day[day] = start_minutes + zone.minutes_per_visit
            candidate.day_end[day] = start + timedelta(minutes=zone.minutes_per_visit)

    Shift.objects.bulk_create(shifts)
    plan.unmet_demand = unmet
    plan.save(update_fields=["unmet_demand"])
    return plan


def _place_tours(account, week_start, plan, capacities, shifts, unmet) -> set[int]:
    """
    Așază fiecare rundă ca un tot: un lucrător, o zi, opriri consecutive.

    All-or-nothing e o decizie, nu o simplificare: o rundă executată pe jumătate
    lasă blocuri necurățate fără ca nimeni să vadă asta în plan.
    """
    from .models import Tour

    tours = (
        Tour.objects.filter(account=account, is_active=True)
        .prefetch_related("stops__zone__site")
    )
    toured: set[int] = set()

    for tour in tours:
        stops = list(tour.stops.select_related("zone__site").order_by("position"))
        if not stops:
            continue
        toured.update(stop.zone_id for stop in stops)

        total = tour.total_minutes
        localities = tour.localities
        for day in _tour_days(tour, week_start):
            reasons: dict[str, str] = {}
            candidate = None
            for cap in sorted(capacities, key=lambda c: -c.remaining):
                reason = _fits(cap, day, total, localities)
                if reason is None:
                    candidate = cap
                    break
                reasons[cap.name] = reason

            if candidate is None:
                unmet.append({
                    "zone": tour.name,
                    "site": f"Rundă · {len(stops)} opriri",
                    "date": day.isoformat(),
                    "minutes": total,
                    "reasons": reasons or {"—": "niciun lucrător cu contract semnat"},
                    "tour": True,
                })
                continue

            cursor = candidate.per_day.get(day, 0)
            for stop in stops:
                cursor += stop.travel_minutes
                start = datetime.combine(day, DAY_START) + timedelta(minutes=cursor)
                shifts.append(Shift(
                    plan=plan, zone=stop.zone, worker_id=candidate.account_id, date=day,
                    start_time=start.time(), duration_minutes=stop.zone.minutes_per_visit,
                    tour=tour, position=stop.position, travel_minutes=stop.travel_minutes,
                ))
                cursor += stop.zone.minutes_per_visit
                candidate.day_end[day] = datetime.combine(day, DAY_START) + timedelta(
                    minutes=cursor
                )
            candidate.used_minutes += total
            candidate.per_day[day] = cursor

    return toured


def _tour_days(tour, week_start: date) -> list[date]:
    allowed = [d for d in sorted(tour.weekdays) if d != SUNDAY]
    if not allowed or tour.visits_per_week == 0:
        return []
    visits = min(tour.visits_per_week, len(allowed))
    step = len(allowed) / visits
    picked = [allowed[int(i * step)] for i in range(visits)]
    return [week_start + timedelta(days=d - 1) for d in picked]


def _visit_days(zone: Zone, week_start: date) -> list[date]:
    """Distribuie vizitele cât mai uniform peste zilele permise, fără duminică."""
    allowed = [d for d in sorted(zone.weekdays) if d != SUNDAY]
    if not allowed:
        return []
    visits = min(zone.visits_per_week, len(allowed))
    if visits == 0:
        return []
    step = len(allowed) / visits
    picked = [allowed[int(i * step)] for i in range(visits)]
    return [week_start + timedelta(days=d - 1) for d in picked]


def capacity_report(account, week_start: date) -> dict:
    """Cerere vs. capacitate, ÎNAINTE de a genera planul."""
    from .models import Tour

    demand = sum(
        z.weekly_minutes
        for z in Zone.objects.filter(
            site__account=account, is_active=True, site__is_active=True
        )
    )
    # Deplasarea dintre opriri e timp de lucru, deci e cerere reală.
    demand += sum(
        stop.travel_minutes * tour.visits_per_week
        for tour in Tour.objects.filter(account=account, is_active=True).prefetch_related("stops")
        for stop in tour.stops.all()
    )
    capacities = build_capacities(account, week_start)
    supply = sum(c.weekly_minutes for c in capacities)
    return {
        "demand_minutes": demand,
        "supply_minutes": supply,
        "workers": len(capacities),
        "deficit_minutes": max(0, demand - supply),
        "utilisation": round(demand / supply * 100, 1) if supply else None,
    }
