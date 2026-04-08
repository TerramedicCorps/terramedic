from django.contrib.gis.db import models
from django.core.validators import RegexValidator


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
            models.UniqueConstraint(
                fields=["country_code", "region_code"],
                name="unique_country_region",
            ),
        ]

    def __str__(self) -> str:
        return self.name
