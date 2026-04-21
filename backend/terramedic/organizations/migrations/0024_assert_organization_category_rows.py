from django.db import migrations


def assert_rows_survived(apps, schema_editor):
    """Sanity-check: every pre-existing (org, category) pair survived
    the table rename in 0023. The rename preserves rows, but a dev
    environment where the old table had unexpected state should fail
    loudly here rather than silently losing data."""
    Organization = apps.get_model("organizations", "Organization")
    OrganizationCategory = apps.get_model(
        "organizations", "OrganizationCategory",
    )
    expected = 0
    for org in Organization.objects.iterator():
        expected += org.categories.count()
    actual = OrganizationCategory.objects.count()
    if expected != actual:
        msg = (
            f"OrganizationCategory row count mismatch after 0023:"
            f" expected {expected} (from Organization.categories)"
            f" but found {actual} through-model rows."
        )
        raise RuntimeError(msg)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0023_organization_category_through"),
    ]

    operations = [
        migrations.RunPython(assert_rows_survived, noop_reverse),
    ]
