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


def test_curly_quotes_are_normalized_to_straight_quotes() -> None:
    fix = _fix("Check the “regen” mode before proceeding.")

    assert fix.steps == 'Check the "regen" mode before proceeding.'


def test_unicode_ellipsis_is_normalized_to_ascii_dots() -> None:
    fix = _fix("Inspect the wiring… then reconnect.")

    assert fix.steps == "Inspect the wiring... then reconnect."


def test_portuguese_prose_with_common_punctuation_is_accepted() -> None:
    fix = _fix(
        "1) Confirmar o diagnóstico: perda de refrigeração & conforto "
        'na cabine (DSG) - ver "manual".'
    )

    assert "diagnóstico" in fix.steps
    assert "&" in fix.steps
    assert '"manual"' in fix.steps


def test_nfd_accents_are_normalized_to_nfc() -> None:
    # c + combining cedilla -> ç ; a + combining tilde -> ã
    nfd = "refrigerac" + "\u0327" + "a" + "\u0303" + "o"
    fix = _fix(f"Verificar {nfd} do sistema.")

    assert "refrigeração" in fix.steps


def test_straight_double_quotes_and_ampersand_are_accepted() -> None:
    fix = _fix('Tools & parts for the "pump" assembly.')

    assert fix.steps == 'Tools & parts for the "pump" assembly.'


def test_script_tag_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        _fix("<script>alert(1)</script>")


def test_angle_brackets_are_still_rejected() -> None:
    with pytest.raises(ValidationError):
        AiKnownIssueResult(**_issue(title="Bad <b>title</b>"))


def test_normalization_does_not_bypass_html_rejection() -> None:
    with pytest.raises(ValidationError):
        _fix("‘<script>’alert(1)‘</script>’")
