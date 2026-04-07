from django.db import migrations, models

CANONICAL_CATEGORIES = [
    ("donate", "Donate"),
    ("volunteer", "Volunteer"),
    ("resource", "Resource"),
    ("everyday", "Everyday"),
    ("career", "Career"),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("organizations", "Category")
    for slug, label in CANONICAL_CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={"label": label},
        )


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("organizations", "Category")
    Category.objects.filter(
        slug__in=[slug for slug, _ in CANONICAL_CATEGORIES],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0005_add_evaluation_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "slug",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("label", models.CharField(max_length=100)),
            ],
            options={
                "ordering": ["slug"],
                "verbose_name_plural": "categories",
            },
        ),
        migrations.RunPython(seed_categories, unseed_categories),
    ]
