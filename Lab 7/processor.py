"""Shipping quotation helpers.

The three public functions below are deliberately defensive: they accept only
well-formed input and raise ``ValueError`` with an explanatory message for
anything else.  The original starter code assumed perfect input, so malformed
strings produced raw ``IndexError`` / ``AttributeError`` / ``TypeError`` /
``JSONDecodeError`` tracebacks (see Lab 7).

Properties enforced by ``test_processor.py``:

* never crash with an unexpected exception type (only ``ValueError`` is used
  to signal invalid input),
* return a non-negative ``float`` for dimensional weight and manifest weight,
* return ``<PREFIX>-<6 digit number>`` for tracking labels.
"""

import json
import math

#: Divisors / limits used by the shipping domain.
DIM_WEIGHT_DIVISOR = 5000.0
_SEPARATORS = {"x": "x", "X": "x", "×": "x", "*": "x", ",": "x"}


def _require_text(value, field_name):
    """Return ``value`` stripped, or raise ``ValueError`` if it is not usable text."""
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


def _parse_positive_dimension(token, axis):
    try:
        number = float(token)
    except (TypeError, ValueError):
        raise ValueError(f"{axis} dimension must be a number, got {token!r}") from None
    if not math.isfinite(number):
        raise ValueError(f"{axis} dimension must be finite, got {token!r}")
    if number <= 0:
        raise ValueError(f"{axis} dimension must be greater than zero, got {token!r}")
    return number


def calculate_dimensional_weight(dimensions_str):
    """Return the volumetric weight ``L*W*H/5000`` for ``"LxWxH"`` input.

    Accepts ``x``/``X``/``,``/``*`` as separators and optional spaces around
    each dimension.  Raises ``ValueError`` for anything that is not exactly
    three positive finite numbers.
    """
    text = _require_text(dimensions_str, "dimensions")

    normalised = text
    for separator, replacement in _SEPARATORS.items():
        normalised = normalised.replace(separator, replacement)

    parts = [part.strip() for part in normalised.split("x")]
    if len(parts) != 3 or any(part == "" for part in parts):
        raise ValueError(
            f"dimensions must be three values in LxWxH format, got {text!r}"
        )

    length = _parse_positive_dimension(parts[0], "length")
    width = _parse_positive_dimension(parts[1], "width")
    height = _parse_positive_dimension(parts[2], "height")

    volume_cm3 = length * width * height
    if not math.isfinite(volume_cm3):
        raise ValueError(f"dimensions are too large to compute a weight: {text!r}")

    return round(volume_cm3 / DIM_WEIGHT_DIVISOR, 2)


def format_tracking_label(raw_code):
    """Normalise ``"e123"`` to ``"E-000123"``.

    The code must be one letter followed by digits; anything else raises
    ``ValueError`` instead of slicing/indexing its way into a crash.
    """
    text = _require_text(raw_code, "tracking code")

    prefix = text[0].upper()
    number_part = text[1:].strip()

    if not prefix.isalpha():
        raise ValueError(
            f"tracking code must start with a letter, got {text!r}"
        )
    if not number_part or not number_part.isdigit():
        raise ValueError(
            f"tracking code must be a letter followed by digits, got {text!r}"
        )

    try:
        tracking_num = int(number_part)
    except (TypeError, ValueError):
        raise ValueError(f"tracking number is not a valid integer: {text!r}") from None

    return f"{prefix}-{tracking_num:06d}"


def parse_package_manifest(json_payload):
    """Return the ``weight`` field of a JSON manifest object as a float."""
    text = _require_text(json_payload, "manifest payload")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"manifest is not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from None

    if not isinstance(data, dict):
        raise ValueError(
            f"manifest must be a JSON object, got {type(data).__name__}"
        )
    if "weight" not in data:
        raise ValueError("manifest is missing the required 'weight' field")

    weight = data["weight"]
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        raise ValueError(
            f"'weight' must be a number, got {type(weight).__name__}: {weight!r}"
        )

    weight = float(weight)
    if not math.isfinite(weight):
        raise ValueError(f"'weight' must be finite, got {weight!r}")
    if weight <= 0:
        raise ValueError(f"'weight' must be greater than zero, got {weight!r}")

    return weight


def _run_step(title, prompt, action, formatter):
    """Ask for one value, run ``action`` on it and report errors without a traceback."""
    print(f"\n==== {title} ====")
    try:
        raw_value = input(prompt)
    except EOFError:
        print("No input received; skipping this step.")
        return
    try:
        print(formatter(action(raw_value)))
    except ValueError as exc:
        print(f"Invalid input: {exc}")


def main():
    _run_step(
        "Running calculate_dimensional_weight",
        "Enter dimensions LxWxH in cm (e.g. 20x30x10): ",
        calculate_dimensional_weight,
        lambda value: f"Dimensional Weight (kg): {value}",
    )
    _run_step(
        "Running format_tracking_label",
        "Enter raw code (e.g. E123): ",
        format_tracking_label,
        lambda value: f"Formatted Label: {value}",
    )
    _run_step(
        "Running parse_package_manifest",
        'Enter manifest JSON (e.g. {"weight": 12.5}): ',
        parse_package_manifest,
        lambda value: f"Manifest Weight: {value}",
    )


if __name__ == "__main__":
    main()
