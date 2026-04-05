from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0003_rename_action_to_everyday"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
