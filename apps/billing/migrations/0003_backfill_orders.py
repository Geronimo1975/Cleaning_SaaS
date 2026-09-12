from django.db import migrations

from apps.billing.backfill import backfill_orders


def forwards(apps, schema_editor):
    backfill_orders(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_order_unique_source_offer"),
        ("marketplace", "0003_servicerequest_dispatch_policy"),
        ("planning", "0006_shift_created_at_shift_updated_at_site_created_at_and_more"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
