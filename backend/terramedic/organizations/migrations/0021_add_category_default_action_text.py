from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0020_add_reviewer_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="default_action_text",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Fallback CTA label used when an OrganizationCategory row"
                    " has no per-(org, category) action_text. Empty string means"
                    " the frontend decides."
                ),
                max_length=80,
            ),
        ),
    ]
