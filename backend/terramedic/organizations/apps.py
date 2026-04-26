from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "terramedic.organizations"

    def ready(self) -> None:
        import terramedic.organizations.signals  # noqa: F401
