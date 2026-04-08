from django.contrib.gis.db import models


class FocusArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
