from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class SDG(models.Model):
    number = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(1), MaxValueValidator(17)],
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["number"]
        verbose_name = "SDG"
        verbose_name_plural = "SDGs"

    def __str__(self) -> str:
        return f"SDG {self.number}: {self.name}"
