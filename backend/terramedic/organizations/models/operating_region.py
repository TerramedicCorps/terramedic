from django.core.validators import RegexValidator
from django.db import models


class OperatingRegion(models.Model):
    country_code = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                r"^[A-Z]{2}$",
                "Must be an ISO 3166-1 alpha-2 code.",
            ),
        ],
    )
    region_code = models.CharField(max_length=10, blank=True, default="")
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["country_code", "name"]
        constraints = [
            # region_code defaults to "" for country-level entries, so this
            # allows at most one country-level row per country code while
            # still permitting multiple sub-national regions.
            models.UniqueConstraint(
                fields=["country_code", "region_code"],
                name="unique_country_region",
            ),
        ]

    def __str__(self) -> str:
        return self.name
