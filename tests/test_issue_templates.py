import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / ".github/ISSUE_TEMPLATE"


def required_textareas(name: str) -> set[str]:
    text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^  - type: ", text)[1:]
    required: set[str] = set()
    for block in blocks:
        if not block.startswith("textarea\n"):
            continue
        identifier = re.search(r"(?m)^    id: ([a-z0-9_]+)$", block)
        if identifier and re.search(
            r"(?ms)^    validations:\n      required: true(?:\n|$)", block
        ):
            required.add(identifier.group(1))
    return required


class IssueTemplateTests(unittest.TestCase):
    def test_feature_form_requires_scope_and_proportionality_boundaries(self) -> None:
        required = required_textareas("feature.yml")
        self.assertTrue(
            {
                "outcome",
                "in_scope",
                "out_of_scope",
                "assurance_boundary",
                "budget_constraints",
                "scope_revision_triggers",
                "acceptance",
            }.issubset(required)
        )

    def test_defect_form_requires_scope_and_proportionality_boundaries(self) -> None:
        required = required_textareas("bug.yml")
        self.assertTrue(
            {
                "observed",
                "expected",
                "reproduction",
                "in_scope",
                "out_of_scope",
                "assurance_boundary",
                "budget_constraints",
                "scope_revision_triggers",
            }.issubset(required)
        )

    def test_decision_form_separates_included_and_excluded_boundary(self) -> None:
        required = required_textareas("decision.yml")
        self.assertTrue(
            {"decision_in_scope", "decision_out_of_scope", "evidence", "options", "authority"}
            .issubset(required)
        )


if __name__ == "__main__":
    unittest.main()
