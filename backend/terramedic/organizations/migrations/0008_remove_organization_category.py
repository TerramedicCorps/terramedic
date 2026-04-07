from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_add_organization_categories"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="organization",
            name="category",
        ),
    ]
