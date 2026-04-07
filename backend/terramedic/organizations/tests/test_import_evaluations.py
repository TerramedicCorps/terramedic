import json
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from terramedic.organizations.models import (
    OrganizationEvaluation,
    ReviewStatus,
)


def _make_evaluation_data(**overrides: Any) -> dict[str, Any]:
    """Build a valid evaluation payload matching curation/schema.json."""
    data: dict[str, Any] = {
        "org_metadata": {
            "name": "Rainforest Alliance",
            "website_url": "https://www.rainforest-alliance.org/",
            "description": "Working to conserve biodiversity.",
        },
        "sdg_alignment": [
            {"sdg": 15, "evidence": "Protects forest ecosystems."},
        ],
        "evidence_of_work": [
            {"activity": "Certified forests.", "type": "conservation"},
        ],
        "accessibility": {
            "categories": ["donate", "volunteer"],
        },
        "evidence_score": {"score": 4, "rationale": "Strong evidence."},
        "curator_notes": {
            "recommendation": "include",
            "notes": "Well-established org.",
        },
        "evaluated_at": "2026-03-15T10:30:00Z",
        "evaluated_by": "claude-opus-4-6",
        "prompt_version": "2026.04.1",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestImportEvaluationsCommand:
    def test_imports_single_file(self, tmp_path: Path) -> None:
        path = tmp_path / "eval.json"
        path.write_text(json.dumps(_make_evaluation_data()))

        call_command("import_evaluations", str(path))

        assert OrganizationEvaluation.objects.count() == 1
        ev = OrganizationEvaluation.objects.first()
        assert ev is not None
        assert ev.org_name == "Rainforest Alliance"
        assert ev.status == ReviewStatus.PENDING

    def test_imports_directory(self, tmp_path: Path) -> None:
        for i in range(3):
            data = _make_evaluation_data(
                org_metadata={
                    "name": f"Org {i}",
                    "website_url": f"https://org{i}.example.com/",
                },
            )
            (tmp_path / f"eval_{i}.json").write_text(json.dumps(data))

        # Add a non-JSON file that should be skipped
        (tmp_path / "readme.txt").write_text("not json")

        call_command("import_evaluations", str(tmp_path))

        assert OrganizationEvaluation.objects.count() == 3

    def test_skips_duplicate_by_name_and_url(
        self,
        tmp_path: Path,
    ) -> None:
        data = _make_evaluation_data()
        path = tmp_path / "eval.json"
        path.write_text(json.dumps(data))

        call_command("import_evaluations", str(path))
        call_command("import_evaluations", str(path))

        assert OrganizationEvaluation.objects.count() == 1

    def test_reports_import_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = tmp_path / "eval.json"
        path.write_text(json.dumps(_make_evaluation_data()))

        call_command("import_evaluations", str(path))

        captured = capsys.readouterr()
        assert "Imported 1" in captured.out

    def test_reports_skip_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        data = _make_evaluation_data()
        path = tmp_path / "eval.json"
        path.write_text(json.dumps(data))

        call_command("import_evaluations", str(path))
        call_command("import_evaluations", str(path))

        captured = capsys.readouterr()
        assert "skipped 1" in captured.out

    def test_invalid_json_reports_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")

        call_command("import_evaluations", str(path))

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert OrganizationEvaluation.objects.count() == 0
