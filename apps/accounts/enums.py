from django.db import models


class EntityType(models.TextChoices):
    """Ce ESTE contul. Imutabil după creare."""

    INDIVIDUAL = "INDIVIDUAL", "Persoană fizică"
    COMPANY = "COMPANY", "Firmă"


class Capability(models.TextChoices):
    """
    Ce POATE FACE contul. Rânduri în AccountCapability, niciodată o coloană `role`.
    O firmă care e și prestator, și cumpărător de materiale primește două rânduri.
    """

    WORKER = "WORKER", "Prestator persoană fizică"
    PROVIDER = "PROVIDER", "Prestator firmă"
    SUPPLIER = "SUPPLIER", "Furnizor de materiale"
    CLIENT = "CLIENT", "Beneficiar"
    EMPLOYER = "EMPLOYER", "Angajator (publică anunțuri)"


class LegalStatus(models.TextChoices):
    """
    Statutul juridic al prestatorului în DE. Dimensiune ORTOGONALĂ față de Capability
    și determină cine e plătitorul legal, cine emite factura și dacă platforma
    poate încasa. Fără el, §35a EStG și Minijob-ul sunt imposibil de administrat.
    """

    UNDECLARED = "UNDECLARED", "Nedeclarat"
    MINIJOB = "MINIJOB", "Minijob în gospodărie (§8a SGB IV)"
    SELBSTSTAENDIG = "SELBSTSTAENDIG", "Selbstständig cu Gewerbeanmeldung"
    KLEINUNTERNEHMER = "KLEINUNTERNEHMER", "Kleinunternehmer (§19 UStG)"
    COMPANY = "COMPANY", "Firmă cu regim normal de TVA"


class AccountStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ciornă"
    PENDING = "PENDING", "În așteptare"
    PUBLISHED = "PUBLISHED", "Publicat"
    SUSPENDED = "SUSPENDED", "Suspendat"
    UNPUBLISHED = "UNPUBLISHED", "Depublicat"


class VerificationLevel(models.IntegerChoices):
    NONE = 0, "Neverificat"
    EMAIL = 1, "Email confirmat"
    PHONE = 2, "Telefon confirmat"
    DOCUMENTS = 3, "Documente verificate"


class MembershipRole(models.TextChoices):
    OWNER = "OWNER", "Proprietar"
    ADMIN = "ADMIN", "Administrator"
    MEMBER = "MEMBER", "Membru"
