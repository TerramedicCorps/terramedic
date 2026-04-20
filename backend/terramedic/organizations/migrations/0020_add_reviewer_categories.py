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
                    "Reviewer-chosen category slugs for the linked"
                    " Organization. NULL means fall back to the AI's"
                    " accessibility.categories list, filtered to known"
                    " Category slugs. Edits here flow through to the"
                    " linked Organization — on the APPROVED transition"
                    " via the create path, and on subsequent admin"
                    " saves via re-sync."
                ),
                null=True,
            ),
        ),
    ]
