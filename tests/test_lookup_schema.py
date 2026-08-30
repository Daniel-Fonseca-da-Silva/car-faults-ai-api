import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.lookup import (
    AiFixResult,
    AiKnownIssueResult,
    IssueSeverity,
    LookupResponse,
)

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "app" / "prompts" / "v1"


def _fix(steps: str, summary: str = "Summary") -> AiFixResult:
    return AiFixResult(summary=summary, steps=steps)


def _issue(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Issue",
        "description": "Description.",
        "severity": IssueSeverity.LOW,
        "fixes": [{"summary": "Fix", "steps": "Steps."}],
    }
    payload.update(overrides)
    return payload


def test_electric_few_shot_example_is_accepted() -> None:
    payload = json.loads((_EXAMPLES_DIR / "electric_example.json").read_text())

    LookupResponse(**payload)


def test_steps_with_apostrophe_and_percent_are_accepted() -> None:
    fix = _fix(
        "i) Confirm that regen pedal isn't engaging above 80% "
        "before checking sensors, or brake system."
    )

    assert "isn't" in fix.steps
    assert "80%" in fix.steps


def test_percent_alone_is_accepted() -> None:
    fix = _fix("Charge to 100% and verify range.")

    assert fix.steps == "Charge to 100% and verify range."


def test_curly_apostrophe_is_normalized_to_ascii() -> None:
    fix = _fix("Confirm the vehicle’s battery isn’t degraded.")

    assert fix.steps == "Confirm the vehicle's battery isn't degraded."


def test_en_dash_is_normalized_to_hyphen() -> None:
    fix = _fix("Torque to 20–25 Nm.")

    assert fix.steps == "Torque to 20-25 Nm."


def test_em_dash_is_normalized_to_hyphen() -> None:
    fix = _fix("Replace the part — then verify.")

    assert fix.steps == "Replace the part - then verify."


def test_curly_quotes_are_stripped_not_passed_through() -> None:
    fix = _fix("Check the “regen” mode before proceeding.")

    assert fix.steps == "Check the regen mode before proceeding."
    assert '"' not in fix.steps
    assert "“" not in fix.steps and "”" not in fix.steps


def test_unicode_ellipsis_is_normalized_to_ascii_dots() -> None:
    fix = _fix("Inspect the wiring… then reconnect.")

    assert fix.steps == "Inspect the wiring... then reconnect."


def test_straight_double_quotes_are_still_rejected() -> None:
    with pytest.raises(ValidationError):
        _fix('Steps with "quoted" text.')


def test_script_tag_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        _fix("<script>alert(1)</script>")


def test_javascript_scheme_with_straight_quotes_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        _fix('javascript:alert("x")')


def test_ampersand_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        _fix("Tools & parts needed.")


def test_angle_brackets_are_still_rejected() -> None:
    with pytest.raises(ValidationError):
        AiKnownIssueResult(**_issue(title="Bad <b>title</b>"))


def test_normalization_does_not_bypass_html_rejection() -> None:
    with pytest.raises(ValidationError):
        _fix("‘<script>’alert(1)‘</script>’")
