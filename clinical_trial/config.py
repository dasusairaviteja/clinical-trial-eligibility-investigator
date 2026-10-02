"""Validate the environment boundary without requiring cloud credentials."""
from enum import StrEnum
from typing import Mapping


class Environment(StrEnum):
    ENG = "ENG"
    TEST = "TEST"
    PROD = "PROD"


def read_environment(values: Mapping[str, str]) -> Environment:
    """Default local runs to ENG; reject typos instead of silently misrouting."""
    value = values.get("APP_ENV", "ENG")
    try:
        return Environment(value)
    except ValueError:
        raise ValueError("APP_ENV must be exactly ENG, TEST, or PROD") from None
