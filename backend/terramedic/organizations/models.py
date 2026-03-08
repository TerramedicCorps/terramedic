from django.contrib.gis.db import models
from parler.models import TranslatableModel, TranslatedFields


class Category(models.TextChoices):
    DONATE = "donate"
    VOLUNTEER = "volunteer"
    RESOURCE = "resource"
    ACTION = "action"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Organization(TranslatableModel):
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    image_url = models.URLField(blank=True, default="")
    category = models.CharField(max_length=20, choices=Category.choices)
    tags = models.ManyToManyField(Tag, blank=True, related_name="organizations")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    location = models.PointField(null=True, blank=True, geography=True)

    translations = TranslatedFields(
        description=models.TextField(),
        action_text=models.CharField(max_length=100),
    )

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
