from django.contrib.gis.db import models


class OperatingRegion(models.Model):
    country_code = models.CharField(max_length=2)
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
