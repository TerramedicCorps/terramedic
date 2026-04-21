import django.db.models.deletion
import parler.fields
import parler.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0022_seed_category_default_action_text"),
    ]

    operations = [
        # Step 1: rename the auto-created M2M join table in place and
        # add the sort_order column. SeparateDatabaseAndState tells
        # Django the new state is "OrganizationCategory exists" while
        # the DB-side change is just a table rename — preserving every
        # existing (org, category) row.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="OrganizationCategory",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("sort_order", models.IntegerField(default=0)),
                        (
                            "organization",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="category_entries",
                                to="organizations.organization",
                            ),
                        ),
                        (
                            "category",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name="organization_entries",
                                to="organizations.category",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name_plural": "organization categories",
                        "ordering": ["sort_order", "category__slug"],
                        "unique_together": {("organization", "category")},
                    },
                    bases=(parler.models.TranslatableModelMixin, models.Model),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE organizations_organization_categories"
                        " RENAME TO organizations_organizationcategory;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE organizations_organizationcategory"
                        " RENAME TO organizations_organization_categories;"
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE organizations_organizationcategory"
                        " ADD COLUMN sort_order integer NOT NULL DEFAULT 0;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE organizations_organizationcategory"
                        " DROP COLUMN sort_order;"
                    ),
                ),
            ],
        ),
        # Step 2: now that OrganizationCategory exists in state, the
        # translation table's master FK can resolve. This is a fresh
        # table — no legacy data to preserve — so a normal CreateModel
        # runs in both state and DB.
        migrations.CreateModel(
            name="OrganizationCategoryTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language_code",
                    models.CharField(
                        db_index=True,
                        max_length=15,
                        verbose_name="Language",
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "action_text",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=80,
                    ),
                ),
                (
                    "master",
                    parler.fields.TranslationsForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="organizations.organizationcategory",
                    ),
                ),
            ],
            options={
                "verbose_name": "organization category Translation",
                "db_table": (
                    "organizations_organizationcategory_translation"
                ),
                "db_tablespace": "",
                "managed": True,
                "default_permissions": (),
                "unique_together": {("language_code", "master")},
            },
            bases=(parler.models.TranslatedFieldsModelMixin, models.Model),
        ),
        # Step 3: flip Organization.categories to declare the explicit
        # through model. State-only — the underlying DB table already
        # exists from step 1.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="organization",
                    name="categories",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="organizations",
                        through="organizations.OrganizationCategory",
                        to="organizations.category",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
