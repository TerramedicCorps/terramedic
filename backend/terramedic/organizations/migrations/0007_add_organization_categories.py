from django.db import migrations, models


def copy_category_to_categories(apps, schema_editor):
    """Copy each org's existing scalar category value into the new M2M."""
    Organization = apps.get_model("organizations", "Organization")
    Category = apps.get_model("organizations", "Category")
    OrganizationCategory = Organization.categories.through  # noqa: N806

    valid_slugs = set(Category.objects.values_list("slug", flat=True))
    through_rows = []

    for org in Organization.objects.iterator():
        if not org.category or org.category not in valid_slugs:
            continue
        through_rows.append(
            OrganizationCategory(
                organization_id=org.id,
                category_id=org.category,
            )
        )

    if through_rows:
        OrganizationCategory.objects.bulk_create(through_rows)


def restore_scalar_category(apps, schema_editor):
    """Restore the scalar category from the M2M using a deterministic choice."""
    Organization = apps.get_model("organizations", "Organization")
    for org in Organization.objects.iterator():
        category = org.categories.order_by("slug").first()
        if not category:
            continue
        org.category = category.slug
        org.save(update_fields=["category"])


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0006_create_category_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="categories",
            field=models.ManyToManyField(
                blank=True,
                related_name="organizations",
                to="organizations.category",
            ),
        ),
        migrations.RunPython(copy_category_to_categories, restore_scalar_category),
    ]
