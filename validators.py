"""Shared input validation helpers (no business logic here).

Rule of thumb used everywhere:
    wrong type  -> TypeError
    wrong value -> ValueError
"""
from __future__ import annotations

import re
from decimal import Decimal

CATEGORIES = ("BIKE", "VAN", "TRUCK")
_USERNAME_RE = re.compile(r"[A-Za-z0-9]{1,25}")


def validate_username(value):
    if not isinstance(value, str):
        raise TypeError("username must be a str")
    if not _USERNAME_RE.fullmatch(value):
        raise ValueError("username must be 1-25 English letters/digits")
    return value


def validate_choice(value, allowed, name="value"):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {tuple(allowed)}")
    return value


def validate_category(value):
    return validate_choice(value, CATEGORIES, "service_category")


def validate_position(value):
    if not isinstance(value, tuple):
        raise TypeError("position must be a tuple")
    if len(value) != 2:
        raise ValueError("position must have exactly two coordinates")
    for coord in value:
        if isinstance(coord, bool) or not isinstance(coord, int):
            raise TypeError("coordinates must be int (bool not allowed)")
    return value


def validate_int(value, name="value", minimum=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int (bool not allowed)")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def validate_positive_decimal(value, name="value"):
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal")
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{name} must be a finite positive Decimal")
    return value


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
