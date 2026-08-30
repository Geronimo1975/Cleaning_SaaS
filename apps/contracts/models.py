"""
Contracte și forme de colaborare.

Granița juridică pe care o codificăm aici:

  ANGAJARE DIRECTĂ  — unitatea e angajatorul, platforma e unealta de HR.
                      Fără licență, fără risc AÜG. Modelul implicit.
  PRESTATOR INDEPENDENT — Dienst-/Werkvertrag cu prestator care are Gewerbe,
                      clienți multipli și preț propriu. Legal doar dacă
                      independența e reală (§7 SGB IV).
  DETAȘARE (AÜG)    — platforma angajează și „împrumută" oamenii unității.
                      Cere Erlaubnis de la Bundesagentur für Arbeit.
                      Blocat în cod până când licența există.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class EngagementModel(models.TextChoices):
    DIRECT_EMPLOYMENT = "DIRECT", "Angajare directă de către unitate"
    INDEPENDENT = "INDEPENDENT", "Prestator independent (Dienst-/Werkvertrag)"
    TEMP_AGENCY = "AUEG", "Detașare de personal (AÜG) — necesită licență"


class ContractType(models.TextChoices):
    VOLLZEIT = "VOLLZEIT", "Contract de muncă — normă întreagă"
    TEILZEIT = "TEILZEIT", "Contract de muncă — part-time"
    MINIJOB = "MINIJOB", "Minijob (până la 40 h/lună)"
    WERKVERTRAG = "WERKVERTRAG", "Contract de prestări servicii"


CONTRACT_ENGAGEMENT = {
    ContractType.VOLLZEIT: EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.TEILZEIT: EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.MINIJOB: EngagementModel.DIRECT_EMPLOYMENT,
    ContractType.WERKVERTRAG: EngagementModel.INDEPENDENT,
}


@dataclass(frozen=True)
class ComplianceIssue:
    """O constatare de conformitate, cu severitate explicită."""

    code: str
    message: str
    blocking: bool

    def __str__(self) -> str:
        return self.message


class WageFloor(models.Model):
    """
    Praguri salariale legale, cu valabilitate în timp — NU constante în cod.
    Se schimbă anual și trebuie actualizate fără deploy.

    `GENERAL`  = gesetzlicher Mindestlohn (§1 MiLoG)
    `GEBAEUDE` = Mindestlohn de ramură, Gebäudereinigung Lohngruppe 1
                 (allgemeinverbindlich — se aplică și firmelor nemembre)
    """

    class Kind(models.TextChoices):
        GENERAL = "GENERAL", "Mindestlohn general"
        GEBAEUDE = "GEBAEUDE", "Mindestlohn Gebäudereinigung LG1"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    hourly_amount = models.DecimalField(max_digits=6, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    source_note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("kind", "-valid_from")

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.hourly_amount} € de la {self.valid_from}"

    @classmethod
    def current(cls, kind, on=None) -> Decimal | None:
        on = on or timezone.localdate()
        row = cls.objects.filter(
            kind=kind, valid_from__lte=on
        ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=on)).first()
        return row.hourly_amount if row else None


class MinijobThreshold(models.Model):
    """
    Geringfügigkeitsgrenze. Din 2022 e dinamică: Mindestlohn × 130 / 3, rotunjită
    în sus. Depășirea o singură lună nu strică nimic; depășirea previzibilă
    transformă Minijob-ul în raport asigurat obligatoriu.
    """

    monthly_limit = models.DecimalField(max_digits=7, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    source_note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("-valid_from",)

    @classmethod
    def current(cls, on=None) -> Decimal | None:
        on = on or timezone.localdate()
        row = cls.objects.filter(valid_from__lte=on).filter(
            models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=on)
        ).first()
        return row.monthly_limit if row else None


class ContractTemplate(models.Model):
    """
    Șablon versionat. Textul semnat NU se ia niciodată de aici la afișare —
    se copiază în ContractDraft.rendered_body la generare. Altfel, o editare
    a șablonului ar rescrie retroactiv contracte deja semnate.
    """

    contract_type = models.CharField(max_length=16, choices=ContractType.choices)
    version = models.CharField(max_length=16)
    language = models.CharField(max_length=5, default="de")
    title = models.CharField(max_length=200)
    body = models.TextField(help_text="Django template. Context: {{ employer }}, {{ worker }} ...")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("contract_type", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("contract_type", "version", "language"), name="uniq_template_version"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_contract_type_display()} v{self.version}"


class DraftStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"
    SENT = "SENT", "Trimis spre semnare"
    SIGNED = "SIGNED", "Semnat"
    DECLINED = "DECLINED", "Refuzat"
    CANCELLED = "CANCELLED", "Anulat"


class ContractDraft(models.Model):
    employer = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="contracts_offered"
    )
    worker = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="contracts_received"
    )
    template = models.ForeignKey(ContractTemplate, on_delete=models.PROTECT)
    contract_type = models.CharField(max_length=16, choices=ContractType.choices)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Gol = nedeterminat")
    hours_per_month = models.DecimalField(max_digits=6, decimal_places=2)
    hourly_wage = models.DecimalField(max_digits=6, decimal_places=2)
    workplace = models.ForeignKey("geo.Locality", on_delete=models.PROTECT)
    probation_months = models.PositiveSmallIntegerField(default=6)
    vacation_days = models.PositiveSmallIntegerField(default=20)

    # Textul efectiv, înghețat la generare.
    rendered_body = models.TextField(blank=True)
    body_sha256 = models.CharField(max_length=64, blank=True)

    status = models.CharField(max_length=12, choices=DraftStatus.choices, default=DraftStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Contract"
        verbose_name_plural = "Contracte"

    def __str__(self) -> str:
        return f"{self.get_contract_type_display()} · {self.worker} @ {self.employer}"

    @property
    def engagement_model(self) -> str:
        return CONTRACT_ENGAGEMENT[self.contract_type]

    @property
    def monthly_gross(self) -> Decimal:
        return (self.hours_per_month * self.hourly_wage).quantize(Decimal("0.01"))

    def compliance_issues(self) -> list[str]:
        """Mesajele verificărilor, pentru afișare. Severitatea: `compliance_report`."""
        return [issue.message for issue in self.compliance_report()]

    def compliance_report(self) -> list["ComplianceIssue"]:
        """
        Verificările care rulează ÎNAINTE de trimiterea spre semnare.

        Severitatea e o proprietate a fiecărei constatări, nu ceva dedus din text.
        Pragul de salariu blochează un contract de muncă, dar doar avertizează la
        un Dienstleistungsvertrag: Mindestlohn-ul de ramură leagă angajatorii,
        nu onorariul unui prestator independent.
        """
        issues: list[ComplianceIssue] = []
        general = WageFloor.current(WageFloor.Kind.GENERAL, self.start_date)
        sector = WageFloor.current(WageFloor.Kind.GEBAEUDE, self.start_date)
        floor = max(x for x in (general, sector) if x is not None) if (general or sector) else None

        is_employment = self.contract_type != ContractType.WERKVERTRAG

        if floor and self.hourly_wage < floor:
            issues.append(ComplianceIssue(
                code="WAGE_FLOOR",
                message=(
                    f"{'Salariul orar' if is_employment else 'Onorariul orar'} "
                    f"{self.hourly_wage} € este sub pragul de {floor} € valabil la "
                    f"{self.start_date:%d.%m.%Y}."
                ),
                blocking=is_employment,
            ))
        if self.contract_type == ContractType.MINIJOB:
            limit = MinijobThreshold.current(self.start_date)
            if limit and self.monthly_gross > limit:
                issues.append(ComplianceIssue(
                    code="MINIJOB_LIMIT",
                    message=(
                        f"Brutul lunar {self.monthly_gross} € depășește pragul Minijob "
                        f"de {limit} €. Raportul devine asigurat obligatoriu."
                    ),
                    blocking=True,
                ))
        if self.engagement_model == EngagementModel.TEMP_AGENCY:
            issues.append(ComplianceIssue(
                code="AUEG_LICENCE",
                message="Detașarea de personal necesită licență AÜG. Blocat.",
                blocking=True,
            ))
        if self.contract_type == ContractType.WERKVERTRAG:
            issues.append(ComplianceIssue(
                code="SCHEINSELBSTSTAENDIGKEIT",
                message=(
                    "Verifică independența reală a prestatorului (Gewerbe activ, clienți "
                    "multipli, preț propriu) — altfel e Scheinselbstständigkeit."
                ),
                blocking=False,
            ))
        return issues

    def clean(self):
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": "Data de final trebuie să fie după cea de start."})


class ContractSignature(models.Model):
    """
    Semnătură electronică simplă (eIDAS art. 25 + §126b BGB Textform).
    Suficientă pentru contracte de prestări servicii și — din ianuarie 2025,
    prin Nachweisgesetz modificat — și pentru documentarea raportului de muncă.
    Semnătura calificată rămâne necesară doar acolo unde legea cere Schriftform.
    """

    contract = models.ForeignKey(ContractDraft, on_delete=models.CASCADE, related_name="signatures")
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT)
    signer_name = models.CharField(max_length=160, help_text="Numele tastat de semnatar")
    signed_at = models.DateTimeField(auto_now_add=True)
    document_sha256 = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ("signed_at",)
        constraints = [
            models.UniqueConstraint(fields=("contract", "account"), name="uniq_signature"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError("Semnătura este imutabilă.")
        super().save(*args, **kwargs)
