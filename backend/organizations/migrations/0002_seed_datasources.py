from django.db import migrations


def seed_datasources(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    DataSource = apps.get_model("organizations", "DataSource")
    org, _ = Organization.objects.get_or_create(
        slug="breathe-esg",
        defaults={"name": "Breathe ESG"},
    )
    for name, source_type in [
        ("SAP ERP", "SAP"),
        ("Utility Bills", "UTILITY"),
        ("Concur Travel", "TRAVEL"),
    ]:
        DataSource.objects.get_or_create(
            organization=org,
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
