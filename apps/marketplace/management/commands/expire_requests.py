"""
Închide cererile la care a trecut termenul de ofertare. De rulat din cron.

Fără un runner, `expire_requests()` era apelat doar din teste, iar în producție
cererile ar fi rămas OPEN la nesfârșit — prestatorii ar fi ofertat la cereri
moarte, iar clientul ar fi primit oferte după ce termenul pe care l-a anunțat
el însuși expirase.
"""

from django.core.management.base import BaseCommand

from apps.marketplace.services import expire_requests


class Command(BaseCommand):
    help = "Trece în EXPIRED cererile al căror termen de ofertare a trecut."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Raportează fără să modifice."
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            from django.utils import timezone

            from apps.marketplace.models import RequestStatus, ServiceRequest

            count = ServiceRequest.objects.filter(
                status=RequestStatus.OPEN, offers_close_at__lte=timezone.now()
            ).count()
            self.stdout.write(f"{count} cereri ar fi expirate.")
            return

        count = expire_requests()
        self.stdout.write(self.style.SUCCESS(f"{count} cereri trecute în EXPIRED."))
