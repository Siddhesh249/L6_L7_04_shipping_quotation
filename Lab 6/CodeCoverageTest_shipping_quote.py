import pytest
from shipping_quote import process_shipments, monitor_container_pressures


# ============================================================================
# Code Coverage Tests for process_shipments
# ============================================================================

def test_single_ground_shipment():
    """Initial starter test: single standard ground shipment with valid parcel."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": False,
            "express_priority": False,
            "packages": [{"weight_kg": 10, "is_hazmat": False}],
        }
    ]
    result = process_shipments(shipments, 20.0)
    assert result["total_quote"] == 60.0
    assert result["status"] == "CLEARED"


def test_invalid_shipments_type():
    """Validates ValueError when shipments argument is not a list."""
    with pytest.raises(ValueError, match="Invalid shipments list or handling fee"):
        process_shipments("not_a_list", 10.0)


def test_negative_handling_fee():
    """Validates ValueError when handling_fee is negative."""
    with pytest.raises(ValueError, match="Invalid shipments list or handling fee"):
        process_shipments([], -5.0)


def test_unapproved_manifest():
    """Validates that shipments with unapproved manifests are skipped."""
    shipments = [
        {"manifest_approved": False, "mode": "ground", "packages": [{"weight_kg": 10}]}
    ]
    result = process_shipments(shipments, 15.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


def test_air_mode_with_express_priority():
    """Validates air mode base rate (12.0) and express priority multiplier (1.25)."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "air",
            "express_priority": True,
            "packages": [{"weight_kg": 10, "is_hazmat": False}],
        }
    ]
    # base_rate = 12.0 -> shipment_cost = 20.0 + (10 * 12.0) = 140.0; express = 140.0 * 1.25 = 175.0
    result = process_shipments(shipments, 20.0)
    assert result["total_quote"] == 175.0
    assert result["status"] == "CLEARED"


def test_ground_mode_heavy_package():
    """Validates heavy package tier (>30kg) charged at 1.5x base rate."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [{"weight_kg": 40, "is_hazmat": False}],
        }
    ]
    # base_rate = 4.0 -> cost = 10.0 + 40 * (4.0 * 1.5) = 250.0
    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 250.0
    assert result["status"] == "CLEARED"


def test_invalid_transport_mode():
    """Validates that invalid transport modes increment rejected_parcels and skip."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "sea",
            "packages": [{"weight_kg": 10}],
        }
    ]
    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


def test_invalid_package_weight():
    """Validates rejection of non-positive package weights (weight <= 0)."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [{"weight_kg": 0}],
        }
    ]
    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 10.0
    assert result["status"] == "CLEARED"


def test_fragile_hazmat_rejection():
    """Validates fragile hazmat parcels trigger immediate shipment cost zeroing and break."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": True,
            "packages": [{"weight_kg": 5, "is_hazmat": True}],
        }
    ]
    result = process_shipments(shipments, 25.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


def test_non_fragile_hazmat():
    """Validates non-fragile hazmat parcel flat surcharge (+50.0)."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": False,
            "packages": [{"weight_kg": 5, "is_hazmat": True}],
        }
    ]
    # shipment_cost = 10.0 + 50.0 = 60.0
    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 60.0
    assert result["status"] == "CLEARED"


def test_flagged_review_threshold():
    """Validates status FLAGGED_REVIEW when rejected_parcels exceeds 3."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": -1},
                {"weight_kg": 0},
                {"weight_kg": 5, "is_hazmat": True},
                {"weight_kg": 5, "is_hazmat": True},
            ],
        }
    ]
    result = process_shipments(shipments, 10.0)
    assert result["status"] == "FLAGGED_REVIEW"


# ============================================================================
# Code Coverage Tests for monitor_container_pressures
# ============================================================================

def test_monitor_container_pressures_no_data():
    """Validates NO_DATA status for empty pressure logs."""
    assert monitor_container_pressures([]) == "NO_DATA"


def test_monitor_container_pressures_leak_detected():
    """Validates LEAK_DETECTED when depressurization streak reaches 2 consecutive readings < 14.0."""
    logs = [
        [15.0, 13.5, 12.8, 15.0]
    ]
    assert monitor_container_pressures(logs) == "LEAK_DETECTED"


def test_monitor_container_pressures_stable_with_recovery():
    """Validates STABLE when low pressure readings do not reach consecutive streak of 2."""
    logs = [
        [13.5, 14.5, 13.8, 14.2],
        [15.0, 15.2]
    ]
    assert monitor_container_pressures(logs) == "STABLE"
