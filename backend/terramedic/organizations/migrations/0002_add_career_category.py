# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="category",
            field=models.CharField(
                choices=[
                    ("donate", "Donate"),
                    ("volunteer", "Volunteer"),
                    ("resource", "Resource"),
                    ("action", "Action"),
                    ("career", "Career"),
                ],
                max_length=20,
            ),
        ),
    ]
