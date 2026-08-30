"""Titlurile conțineau entități HTML și ieșeau dublu-escapate la randare."""

import importlib

from django.db import migrations

seed = importlib.import_module("apps.contracts.migrations.0003_seed_templates")


class Migration(migrations.Migration):
    dependencies = [("contracts", "0003_seed_templates")]
    operations = [migrations.RunPython(seed.forwards, migrations.RunPython.noop)]
