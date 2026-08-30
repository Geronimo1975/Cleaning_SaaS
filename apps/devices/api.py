"""
Endpoint de ingestie pentru echipamente.

Autentificare prin cheie de aparat în antetul `Authorization: Bearer`, nu prin
sesiune: aparatul nu are utilizator. Cheia se compară pe hash, deci o citire a
bazei de date nu permite emiterea de telemetrie falsă.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import TelemetryError, authenticate_device, ingest_session


@csrf_exempt
@require_POST
def ingest(request):
    raw_token = _bearer(request)
    try:
        device = authenticate_device(raw_token)
    except TelemetryError as exc:
        return JsonResponse({"error": str(exc)}, status=401)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON invalid."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Se așteaptă un obiect JSON."}, status=400)

    try:
        session, created = ingest_session(device, payload)
    except TelemetryError as exc:
        return JsonResponse({"error": str(exc)}, status=422)

    return JsonResponse(
        {
            "id": session.pk,
            "created": created,
            "matched_shift": session.shift_id,
            "runtime_minutes": session.runtime_minutes,
        },
        status=201 if created else 200,
    )


def _bearer(request) -> str:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""
