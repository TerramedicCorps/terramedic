import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from terramedic.organizations.models import OrganizationEvaluation


class Command(BaseCommand):
    help = "Import curation evaluation JSON files into the database"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "path",
            help="Path to a JSON file or directory of JSON files.",
        )

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        path = Path(str(options["path"]))

        if path.is_dir():
            files = sorted(path.glob("*.json"))
        elif path.is_file() and path.suffix == ".json":
            files = [path]
        else:
            raise CommandError(
                f"{path} is not a JSON file or directory.",
            )

        imported = 0
        skipped = 0

        for file_path in files:
            try:
                data = json.loads(file_path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                self.stderr.write(
                    self.style.ERROR(f"Error reading {file_path}: {exc}"),
                )
                continue

            name = data.get("org_metadata", {}).get("name", "")
            url = data.get("org_metadata", {}).get("website_url", "")

            if not name or not url:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error: {file_path} missing org_metadata.name or website_url.",
                    ),
                )
                continue

            exists = OrganizationEvaluation.objects.filter(
                evaluation_data__org_metadata__name=name,
                evaluation_data__org_metadata__website_url=url,
            ).exists()

            if exists:
                skipped += 1
                continue

            OrganizationEvaluation.objects.create(evaluation_data=data)
            imported += 1

        parts = [f"Imported {imported} evaluation(s)"]
        if skipped:
            parts.append(f"skipped {skipped} duplicate(s)")
        self.stdout.write(self.style.SUCCESS(", ".join(parts) + "."))
