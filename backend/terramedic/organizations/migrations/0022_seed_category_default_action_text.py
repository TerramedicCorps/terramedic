from django.db import migrations

CANONICAL_DEFAULTS = [
    ("donate", "Learn more"),
    ("volunteer", "Volunteer"),
    ("resource", "Explore resources"),
    ("everyday", "Take action"),
    ("career", "Browse jobs"),
]


def seed_defaults(apps, schema_editor):
    Category = apps.get_model("organizations", "Category")
    for slug, text in CANONICAL_DEFAULTS:
        Category.objects.filter(slug=slug).update(default_action_text=text)


def unseed_defaults(apps, schema_editor):
    Category = apps.get_model("organizations", "Category")
    Category.objects.filter(
        slug__in=[slug for slug, _ in CANONICAL_DEFAULTS],
    ).update(default_action_text="")


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0021_add_category_default_action_text"),
    ]

    operations = [
        migrations.RunPython(seed_defaults, unseed_defaults),
    ]
