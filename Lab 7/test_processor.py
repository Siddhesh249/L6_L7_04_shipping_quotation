"""Property-based fuzz tests for the shipping quotation processor.

Each ``*_no_crash`` test asserts that the function under test never dies with an
unexpected exception.  A ``ValueError`` is treated as a *valid* rejection: the
hardened implementation is allowed to refuse malformed input, but it must do so
deliberately instead of leaking ``IndexError`` / ``AttributeError`` /
``TypeError`` / ``JSONDecodeError`` tracebacks.

The remaining tests pin down the happy-path behaviour of the same functions so
that hardening the code does not break valid input.
"""

import json

import pytest
from hypothesis import given, strategies as st

from processor import (
    calculate_dimensional_weight,
    format_tracking_label,
    parse_package_manifest,
)


def _call_no_crash(func, value):
    """Call ``func(value)``; ValueError means "rejected", anything else is a bug."""
    try:
        return func(value)
    except ValueError:
        return None
    except Exception as exc:  # noqa: BLE001 - deliberately broad: that is the point
        raise AssertionError(
            f"{func.__name__} crashed with {type(exc).__name__}: {exc} for input {value!r}"
        ) from exc


@given(st.text() | st.none())
def test_calculate_dimensional_weight_no_crash(s):
    """Arbitrary text / None must not produce an unexpected traceback."""
    result = _call_no_crash(calculate_dimensional_weight, s)
    if result is not None:
        assert isinstance(result, float), f"expected float, got {type(result).__name__}"
        assert result >= 0, f"dimensional weight must be non-negative, got {result}"


@given(st.text() | st.none())
def test_format_tracking_label_safe(s):
    """Arbitrary text / None must not produce an unexpected traceback."""
    result = _call_no_crash(format_tracking_label, s)
    if result is not None:
        assert isinstance(result, str), f"expected str, got {type(result).__name__}"
        prefix, _, number = result.partition("-")
        assert len(prefix) == 1 and prefix.isalpha(), f"bad prefix in {result!r}"
        assert number.isdigit(), f"bad tracking number in {result!r}"


@given(st.text() | st.none())
def test_parse_package_manifest_safe(s):
    """Arbitrary text / None must not produce an unexpected traceback."""
    result = _call_no_crash(parse_package_manifest, s)
    if result is not None:
        assert isinstance(result, float), f"expected float, got {type(result).__name__}"
        assert result >= 0, f"manifest weight must be non-negative, got {result}"


@given(
    st.integers(min_value=1, max_value=500),
    st.integers(min_value=1, max_value=500),
    st.integers(min_value=1, max_value=500),
)
def test_dimensional_weight_happy_path(length, width, height):
    """Valid integer dimensions are converted with the /5000 divisor."""
    expected = round((length * width * height) / 5000.0, 2)
    assert calculate_dimensional_weight(f"{length}x{width}x{height}") == expected


@given(
    st.integers(min_value=1, max_value=500),
    st.integers(min_value=1, max_value=500),
    st.integers(min_value=1, max_value=500),
    st.sampled_from(["x", "X", ",", " * "]),
)
def test_dimensional_weight_separator_variants(length, width, height, sep):
    """The common separator spellings all describe the same box."""
    expected = round((length * width * height) / 5000.0, 2)
    raw = sep.join(str(v) for v in (length, width, height))
    assert calculate_dimensional_weight(raw) == expected


@given(st.integers(min_value=0, max_value=999_999), st.sampled_from("ABCDEFGHJKLMNPQRSTUVWXYZ"))
def test_tracking_label_happy_path(tracking_number, prefix):
    """Lower-case input is normalised to ``<PREFIX>-<6 digit number>``."""
    label = format_tracking_label(f"{prefix.lower()}{tracking_number}")
    assert label == f"{prefix}-{tracking_number:06d}"


@given(st.floats(min_value=0.01, max_value=10_000, allow_nan=False, allow_infinity=False))
def test_manifest_weight_happy_path(weight):
    """A well-formed JSON manifest returns the numeric weight."""
    payload = json.dumps({"weight": weight})
    assert parse_package_manifest(payload) == pytest.approx(float(weight))
