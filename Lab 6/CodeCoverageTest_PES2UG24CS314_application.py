
import pytest

from hospital_triage_priority import (
    process_triage_wards,
    monitor_oxygen_manifolds,
)


def test_invalid_wards_type():
    with pytest.raises(ValueError):
        process_triage_wards("invalid", 10)


def test_negative_default_acuity():
    with pytest.raises(ValueError):
        process_triage_wards([], -1)


def test_empty_wards_returns_no_urgent_cases():
    result = process_triage_wards([], 10)

    assert result == {
        "acuity_score": 0,
        "status": "NO_URGENT_CASES",
    }


def test_non_accepting_ward_is_skipped():
    wards = [
        {
            "is_accepting": False,
            "tier": "general",
            "patients": [{"spo2": 80, "hr": 140}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_accepted_ward_without_patients():
    wards = [{"is_accepting": True}]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_invalid_spo2_is_flagged():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 0, "hr": 75}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_invalid_heart_rate_is_flagged():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 0}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_unconscious_general_ward_patient():
    wards = [
        {
            "is_accepting": True,
            "tier": "general",
            "patients": [
                {"spo2": 98, "hr": 75, "unconscious": True}
            ],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 100
    assert result["status"] == "TRIAGE_STABLE"


def test_unconscious_outpatient_resets_acuity():
    wards = [
        {
            "is_accepting": True,
            "tier": "outpatient",
            "patients": [
                {"spo2": 98, "hr": 75, "unconscious": False},
                {"spo2": 98, "hr": 75, "unconscious": True},
                {"spo2": 80, "hr": 140, "unconscious": False},
            ],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_low_oxygen_increases_acuity():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 89, "hr": 75}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 60


def test_high_heart_rate_increases_acuity():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 95, "hr": 121}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 60


def test_normal_patient_uses_default_acuity():
    wards = [
        {
            "is_accepting": True,
            "tier": "general",
            "patients": [
                {"spo2": 98, "hr": 72, "unconscious": False}
            ],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result == {
        "acuity_score": 10,
        "status": "TRIAGE_STABLE",
    }


def test_icu_standby_adds_acuity():
    wards = [
        {
            "is_accepting": True,
            "icu_standby": True,
            "patients": [
                {"spo2": 98, "hr": 72, "unconscious": False}
            ],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 35
    assert result["status"] == "TRIAGE_STABLE"


def test_more_than_four_flagged_entries_triggers_alert():
    patients = [{"spo2": 0, "hr": 75} for _ in range(5)]
    wards = [{"is_accepting": True, "patients": patients}]

    result = process_triage_wards(wards, 10)

    assert result == {
        "acuity_score": 0,
        "status": "WARD_ALERT",
    }


def test_empty_sensor_stream_returns_no_data():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"


def test_two_consecutive_low_pressure_readings_fail():
    assert monitor_oxygen_manifolds([[3.5, 3.8]]) == "PRESSURE_FAILURE"


def test_single_low_pressure_reading_is_not_failure():
    assert monitor_oxygen_manifolds([[3.5]]) == "PRESSURE_NORMAL"


def test_normal_pressure_returns_normal():
    assert monitor_oxygen_manifolds([[4.5, 5.0]]) == "PRESSURE_NORMAL"


def test_normal_reading_resets_low_pressure_streak():
    assert (
        monitor_oxygen_manifolds([[3.5, 4.5, 3.8]])
        == "PRESSURE_NORMAL"
    )


def test_each_manifold_has_its_own_streak():
    assert (
        monitor_oxygen_manifolds([[3.5], [3.5]])
        == "PRESSURE_NORMAL"
    )
