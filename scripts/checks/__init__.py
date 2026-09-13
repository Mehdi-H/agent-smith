"""Shared contracts for repository feedback checks."""

from .core import (
    Check,
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Problem,
    Violation,
    run_check,
)

__all__ = [
    "Check",
    "CheckResult",
    "IncompleteCheck",
    "InvalidTarget",
    "Location",
    "Problem",
    "Violation",
    "run_check",
]
