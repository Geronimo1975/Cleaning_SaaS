"""Golește coada de notificări către Google Indexing API. De rulat din cron."""

from django.core.management.base import BaseCommand

from apps.jobs.indexing import flush


class Command(BaseCommand):
    help = "Trimite notificările de indexare în așteptare către Google."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        report = flush(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(str(report)))
