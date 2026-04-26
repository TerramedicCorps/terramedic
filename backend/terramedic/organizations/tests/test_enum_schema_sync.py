import json
from pathlib import Path

from terramedic.organizations.models import (
    EngagementType,
    GeographicScope,
    TimeCommitment,
)

_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[3] / "curation" / "schema.json")
    .read_text(),
)


class TestEnumSchemaSync:
    """Enum values stay in sync with curation/schema.json."""

    def test_geographic_scope_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"]["geographic_coverage"][
            "properties"
        ]["scope"]["enum"]
        model_values = [c.value for c in GeographicScope]
        assert set(model_values) == set(schema_values)

    def test_engagement_type_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"][
            "engagement_opportunities"
        ]["items"]["properties"]["engagement_type"]["enum"]
        model_values = [c.value for c in EngagementType]
        assert set(model_values) == set(schema_values)

    def test_time_commitment_matches_schema(self) -> None:
        schema_values = _SCHEMA["properties"][
            "engagement_opportunities"
        ]["items"]["properties"]["time_commitment"]["enum"]
        model_values = [c.value for c in TimeCommitment]
        assert set(model_values) == set(schema_values)
