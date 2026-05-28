import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the superuser from env vars on every deploy."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME/PASSWORD not set — skipping.")
            return
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_superuser": True, "is_staff": True},
        )
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} superuser: {username}")
