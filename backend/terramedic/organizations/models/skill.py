from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
