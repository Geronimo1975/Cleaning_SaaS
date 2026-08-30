"""
Echipamente digitalizate și telemetrie.

O precizare care decide toată proiectarea: **timpul de funcționare al unui
aspirator nu este timpul de curățenie.** Într-o vizită de 120 de minute,
aspiratorul poate merge 25 — restul e praf, băi, geamuri, deplasare între
etaje. Telemetria nu înlocuiește pontajul.

Ce face în schimb, și ce pontajul singur nu poate face:
  * confirmă că munca a avut loc, independent de cine apasă un buton,
  * arată DISCREPANȚE — pontaj 90 min, aspirator 8 min e o întrebare,
  * dă o limită inferioară obiectivă a timpului lucrat.

De aceea telemetria e sursă de VERIFICARE, nu sursă de calibrare.
"""

import hashlib
import secrets

from django.db import models
from django.utils import timezone


class DeviceKind(models.TextChoices):
    VACUUM = "VACUUM", "Aspirator"
    SCRUBBER = "SCRUBBER", "Mașină de spălat pardoseli"
    POLISHER = "POLISHER", "Mașină de lustruit"
    STEAM = "STEAM", "Aparat cu abur"
    OTHER = "OTHER", "Alt echipament"


class DeviceStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "În funcțiune"
    MAINTENANCE = "MAINTENANCE", "În service"
    RETIRED = "RETIRED", "Scos din uz"


class Device(models.Model):
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="devices"
    )
    kind = models.CharField(max_length=12, choices=DeviceKind.choices, default=DeviceKind.VACUUM)
    label = models.CharField(max_length=96, help_text="Numele de pe autocolant")
    manufacturer = models.CharField(max_length=96, blank=True)
    model_name = models.CharField(max_length=96, blank=True)
    serial_number = models.CharField(max_length=96, blank=True)

    site = models.ForeignKey(
        "planning.Site", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="devices", help_text="Obiectivul unde staționează",
    )
    status = models.CharField(
        max_length=12, choices=DeviceStatus.choices, default=DeviceStatus.ACTIVE
    )

    # Cheia de ingestie e stocată doar ca hash. Se afișează o singură dată.
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    token_prefix = models.CharField(max_length=8, editable=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("label",)
        verbose_name = "Echipament"
        verbose_name_plural = "Echipamente"

    def __str__(self) -> str:
        return f"{self.label} ({self.get_kind_display()})"

    @staticmethod
    def hash_token(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    def issue_token(self) -> str:
        """Generează o cheie nouă și o returnează O SINGURĂ DATĂ."""
        raw = secrets.token_urlsafe(32)
        self.token_hash = self.hash_token(raw)
        self.token_prefix = raw[:8]
        self.save(update_fields=["token_hash", "token_prefix"])
        return raw

    def touch(self):
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])

    @property
    def is_online(self) -> bool:
        if not self.last_seen_at:
            return False
        return (timezone.now() - self.last_seen_at).total_seconds() < 86400


class TelemetrySession(models.Model):
    """
    O perioadă de funcționare raportată de echipament.

    `external_id` face ingestia idempotentă: un aparat care retrimite după o
    pană de rețea nu dublează datele.
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="sessions")
    external_id = models.CharField(max_length=64)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    runtime_minutes = models.PositiveSmallIntegerField()
    area_sqm = models.PositiveIntegerField(null=True, blank=True)
    battery_start = models.PositiveSmallIntegerField(null=True, blank=True)
    battery_end = models.PositiveSmallIntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=32, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    # Legătura cu planificarea, stabilită la ingestie dacă se poate.
    shift = models.ForeignKey(
        "planning.Shift", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="telemetry_sessions",
    )
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-started_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("device", "external_id"), name="uniq_session_per_device"
            )
        ]
        indexes = [models.Index(fields=("device", "started_at"))]
        verbose_name = "Sesiune telemetrie"
        verbose_name_plural = "Sesiuni telemetrie"

    def __str__(self) -> str:
        return f"{self.device.label} · {self.started_at:%d.%m %H:%M} · {self.runtime_minutes} min"

    @property
    def date(self):
        return timezone.localtime(self.started_at).date()
