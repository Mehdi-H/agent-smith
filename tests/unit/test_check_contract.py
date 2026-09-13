"""Define the common process contract shared by Python feedback checks."""

from io import StringIO
from pathlib import Path

from scripts.checks.core import CheckResult, Location, Violation, run_check


class PassingCheck:
    name = "Example check"

    def evaluate(self, target: Path) -> CheckResult:
        return CheckResult()


class FailingCheck:
    name = "Example check"

    def evaluate(self, target: Path) -> CheckResult:
        return CheckResult(
            (
                Violation(
                    "replace the invalid value",
                    Location(target, line=7, symbol="setting"),
                    rule="invalid-value",
                ),
            )
        )


class CrashingCheck:
    name = "Example check"

    def evaluate(self, target: Path) -> CheckResult:
        raise OSError("dependency unavailable")


def test_success_is_silent_and_returns_zero(tmp_path: Path) -> None:
    # Given a check that finds no problems in its target.
    diagnostics = StringIO()
    # When the shared runner evaluates it.
    status = run_check(PassingCheck(), tmp_path, diagnostics)
    # Then the process contract is a silent zero.
    assert status == 0
    assert diagnostics.getvalue() == ""


def test_problems_are_structured_rendered_and_return_one(tmp_path: Path) -> None:
    # Given a check that identifies one rule violation at a source location.
    diagnostics = StringIO()
    # When the shared runner evaluates it.
    status = run_check(FailingCheck(), tmp_path / "settings.toml", diagnostics)
    # Then the typed problem becomes one actionable diagnostic and status one.
    assert status == 1
    assert diagnostics.getvalue() == (
        f"{tmp_path / 'settings.toml'}:7:setting: [invalid-value] replace the invalid value\n"
    )


def test_unexpected_exceptions_fail_closed(tmp_path: Path) -> None:
    # Given a check whose evaluation cannot complete.
    diagnostics = StringIO()
    # When the shared runner catches the implementation error.
    status = run_check(CrashingCheck(), tmp_path, diagnostics)
    # Then incomplete work cannot be mistaken for success.
    assert status == 1
    assert diagnostics.getvalue() == "Example check could not complete: dependency unavailable\n"
