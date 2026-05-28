from django.db import migrations


def seed_datasources(apps, schema_editor):
    DataSource = apps.get_model("organizations", "DataSource")
    for name, source_type in [
        ("SAP ERP", "SAP"),
        ("Utility Bills", "UTILITY"),
        ("Concur Travel", "TRAVEL"),
    ]:
        DataSource.objects.get_or_create(
            source_type=source_type,
            defaults={"name": name, "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_datasources, migrations.RunPython.noop),
    ]
