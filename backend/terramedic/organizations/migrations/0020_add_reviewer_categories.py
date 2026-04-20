from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0019_remove_action_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationevaluation",
            name="reviewer_categories",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text=(
                    "Reviewer-chosen category slugs for the created"
                    " Organization. NULL means fall back to the AI's"
                    " accessibility.categories list, filtered to known"
                    " Category slugs."
                ),
                null=True,
            ),
        ),
    ]
