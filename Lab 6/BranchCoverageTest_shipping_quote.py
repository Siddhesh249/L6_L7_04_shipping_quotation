import pytest
from shipping_quote import process_shipments, monitor_container_pressures


# ============================================================================
# Branch Coverage Tests for process_shipments
# ============================================================================

def test_single_ground_shipment_cleared():
    """Validates basic standard ground shipment clearing with valid quote."""
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
    assert result == {"total_quote": 60.0, "status": "CLEARED"}


def test_invalid_shipments_type():
    """Validates ValueError when shipments is not a list (evaluates first condition of OR)."""
    with pytest.raises(ValueError, match="Invalid shipments list or handling fee"):
        process_shipments("not_a_list", 10.0)


def test_negative_handling_fee():
    """Validates ValueError when shipments is a list but handling_fee < 0 (evaluates second condition of OR)."""
    with pytest.raises(ValueError, match="Invalid shipments list or handling fee"):
        process_shipments([], -1.0)


def test_empty_shipments_list():
    """Validates that empty shipments list results in NO_CARGO without entering the loop."""
    result = process_shipments([], 10.0)
    assert result == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_unapproved_manifest():
    """Validates that shipments with unapproved manifest branch into 'continue'."""
    shipments = [
        {"manifest_approved": False, "mode": "ground", "packages": [{"weight_kg": 10}]}
    ]
    result = process_shipments(shipments, 15.0)
    assert result == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_air_mode_with_express_priority():
    """Validates 'air' transport mode rate (12.0) and express_priority multiplier (1.25)."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "air",
            "express_priority": True,
            "packages": [{"weight_kg": 10, "is_hazmat": False}],
        }
    ]
    # base_rate = 12.0 -> shipment_cost = (20.0 + 10 * 12.0) * 1.25 = 175.0
    result = process_shipments(shipments, 20.0)
    assert result == {"total_quote": 175.0, "status": "CLEARED"}


def test_ground_mode_default_and_heavy_package():
    """Validates default transport mode ('ground', rate 4.0) and heavy package tier (>30kg, 1.5x rate)."""
    shipments = [
        {
            "manifest_approved": True,
            # mode omitted to test default 'ground'
            "packages": [{"weight_kg": 40, "is_hazmat": False}],
        }
    ]
    # base_rate = 4.0 -> cost = 10.0 + 40 * (4.0 * 1.5) = 250.0
    result = process_shipments(shipments, 10.0)
    assert result == {"total_quote": 250.0, "status": "CLEARED"}


def test_invalid_transport_mode():
    """Validates else branch for unknown transport mode (rejected_parcels incremented, shipment skipped)."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "train",
            "packages": [{"weight_kg": 10}],
        }
    ]
    result = process_shipments(shipments, 10.0)
    assert result == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_empty_packages_list():
    """Validates shipment with empty packages list skips the inner package loop."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [],
        }
    ]
    # Only handling fee is charged
    result = process_shipments(shipments, 15.0)
    assert result == {"total_quote": 15.0, "status": "CLEARED"}


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
    assert result == {"total_quote": 10.0, "status": "CLEARED"}


def test_fragile_hazmat_break():
    """Validates fragile hazmat parcels zero shipment cost and break out of package loop immediately."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": True,
            "packages": [
                {"weight_kg": 5, "is_hazmat": True},
                {"weight_kg": 10, "is_hazmat": False},  # Should be skipped due to break
            ],
        }
    ]
    result = process_shipments(shipments, 25.0)
    assert result == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_non_fragile_hazmat():
    """Validates non-fragile hazmat parcel applies flat 50.0 surcharge."""
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
    assert result == {"total_quote": 60.0, "status": "CLEARED"}


def test_flagged_review_threshold():
    """Validates FLAGGED_REVIEW status when rejected_parcels strictly exceeds 3."""
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": -1},                     # 1
                {"weight_kg": 0},                      # 2
                {"weight_kg": 5, "is_hazmat": True},   # 3
                {"weight_kg": 5, "is_hazmat": True},   # 4 (> 3)
            ],
        }
    ]
    result = process_shipments(shipments, 10.0)
    assert result["status"] == "FLAGGED_REVIEW"


# ============================================================================
# Branch Coverage Tests for monitor_container_pressures
# ============================================================================

def test_monitor_container_pressures_no_data():
    """Validates NO_DATA returned for empty list and None."""
    assert monitor_container_pressures([]) == "NO_DATA"
    assert monitor_container_pressures(None) == "NO_DATA"


def test_monitor_container_pressures_leak_detected():
    """Validates LEAK_DETECTED when consecutive depressurization readings reach 2."""
    logs = [
        [15.0, 13.5, 12.8, 15.0]
    ]
    assert monitor_container_pressures(logs) == "LEAK_DETECTED"


def test_monitor_container_pressures_streak_reset_to_stable():
    """Validates STABLE when low pressure readings are interrupted and streak resets to 0."""
    logs = [
        [13.5, 14.5, 13.8, 14.2],  # Streak dips to 1 but resets each time
        [15.0, 15.2],
    ]
    assert monitor_container_pressures(logs) == "STABLE"


def test_monitor_container_pressures_single_dip_at_end_of_container():
    """Validates container ending with streak == 1 proceeds to STABLE without triggering leak."""
    logs = [
        [15.0, 13.2]  # Ends at streak 1
    ]
    assert monitor_container_pressures(logs) == "STABLE"
