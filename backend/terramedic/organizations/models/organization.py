from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from parler.models import TranslatableModel, TranslatedFields

from terramedic.organizations.models.category import Category
from terramedic.organizations.models.enums import GeographicScope
from terramedic.organizations.models.focus_area import FocusArea
from terramedic.organizations.models.operating_region import OperatingRegion
from terramedic.organizations.models.tag import Tag


class Organization(TranslatableModel):
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    image_url = models.URLField(blank=True, default="")
    categories = models.ManyToManyField(
        Category,
        related_name="organizations",
        blank=True,
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="organizations",
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    location = models.PointField(null=True, blank=True, geography=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    # Enrichment fields
    geographic_scope = models.CharField(
        max_length=20,
        choices=GeographicScope.choices,
        blank=True,
        default="",
    )
    year_founded = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(2100),
        ],
    )
    legal_status = models.CharField(
        max_length=100, blank=True, default="",
    )
    evidence_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
    )
    donate_url = models.URLField(blank=True, default="")
    volunteer_url = models.URLField(blank=True, default="")
    toolkit_url = models.URLField(blank=True, default="")
    focus_areas = models.ManyToManyField(
        FocusArea,
        blank=True,
        related_name="organizations",
    )
    operating_regions = models.ManyToManyField(
        OperatingRegion,
        blank=True,
        related_name="organizations",
    )

    translations = TranslatedFields(
        description=models.TextField(),
        action_text=models.CharField(max_length=100),
    )

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
