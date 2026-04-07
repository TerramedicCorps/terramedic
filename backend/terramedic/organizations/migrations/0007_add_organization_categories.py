from django.db import migrations, models


def copy_category_to_categories(apps, schema_editor):
    """Copy each org's existing scalar category value into the new M2M."""
    Organization = apps.get_model("organizations", "Organization")
    Category = apps.get_model("organizations", "Category")
    for org in Organization.objects.all():
        if not org.category:
            continue
        try:
            cat = Category.objects.get(slug=org.category)
        except Category.DoesNotExist:
            continue
        org.categories.add(cat)


def noop_reverse(apps, schema_editor):
    """Nothing to do on reverse — the scalar field still holds the data."""


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
        migrations.RunPython(copy_category_to_categories, noop_reverse),
    ]
