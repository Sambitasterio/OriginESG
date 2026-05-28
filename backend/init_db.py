"""
Runs on every Railway deploy after migrations.
Creates or updates the superuser and seeds default data sources.
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breathe_esg.settings")

import django
django.setup()

from django.contrib.auth.models import User
from organizations.models import DataSource, Organization

# ── Superuser ─────────────────────────────────────────────────────────────────
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "changeme123")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

user, created = User.objects.get_or_create(
    username=username,
    defaults={"email": email, "is_superuser": True, "is_staff": True},
)
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()
print(f"{'Created' if created else 'Updated'} superuser: {username}", flush=True)

# ── Default org + data sources ────────────────────────────────────────────────
org, _ = Organization.objects.get_or_create(
    slug="default",
    defaults={"name": "Breathe ESG"},
)

for name, source_type in [
    ("SAP ERP", "SAP"),
    ("Utility Bills", "UTILITY"),
    ("Concur Travel", "TRAVEL"),
]:
    ds, ds_created = DataSource.objects.get_or_create(
        organization=org,
        source_type=source_type,
        defaults={"name": name, "is_active": True},
    )
    if ds_created:
        print(f"Created data source: {name}", flush=True)

print("init_db done.", flush=True)
