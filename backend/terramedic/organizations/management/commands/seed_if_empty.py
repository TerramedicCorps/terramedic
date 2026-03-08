from django.core.management import call_command
from django.core.management.base import BaseCommand

from terramedic.organizations.models import Organization


class Command(BaseCommand):
    help = "Load seed data fixture if no organizations exist"

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        if Organization.objects.exists():
            self.stdout.write("Data already exists, skipping seed.")
            return
        call_command("loaddata", "seed_data")
        self.stdout.write(self.style.SUCCESS("Seed data loaded."))
