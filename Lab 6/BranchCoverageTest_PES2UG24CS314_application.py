
import pytest

from hospital_triage_priority import (
    process_triage_wards,
    monitor_oxygen_manifolds,
)


def test_validation_rejects_non_list_wards():
    with pytest.raises(ValueError):
        process_triage_wards(None, 10)


def test_validation_rejects_negative_acuity():
    with pytest.raises(ValueError):
        process_triage_wards([], -1)


def test_valid_empty_wards():
    assert process_triage_wards([], 10) == {
        "acuity_score": 0,
        "status": "NO_URGENT_CASES",
    }


def test_ward_acceptance_true_and_false():
    wards = [
        {
            "is_accepting": False,
            "patients": [{"spo2": 98, "hr": 70}],
        },
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 70}],
        },
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 10
    assert result["status"] == "TRIAGE_STABLE"


def test_ward_with_no_patients():
    result = process_triage_wards(
        [{"is_accepting": True, "patients": []}], 10
    )

    assert result["status"] == "NO_URGENT_CASES"


def test_both_invalid_vitals():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 0, "hr": 0}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_invalid_heart_rate_with_valid_spo2():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 0}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0


def test_unconscious_general_patient():
    wards = [
        {
            "is_accepting": True,
            "tier": "general",
            "patients": [{"spo2": 98, "hr": 75, "unconscious": True}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 100
    assert result["status"] == "TRIAGE_STABLE"


def test_unconscious_outpatient_breaks_patient_loop():
    wards = [
        {
            "is_accepting": True,
            "tier": "outpatient",
            "patients": [
                {"spo2": 98, "hr": 75},
                {"spo2": 98, "hr": 75, "unconscious": True},
                {"spo2": 80, "hr": 140},
            ],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_low_spo2_triggers_high_acuity():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 89, "hr": 75}],
        }
    ]

    assert process_triage_wards(wards, 10)["acuity_score"] == 60


def test_high_heart_rate_triggers_high_acuity():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 95, "hr": 121}],
        }
    ]

    assert process_triage_wards(wards, 10)["acuity_score"] == 60


def test_normal_vitals_use_default_acuity():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 95, "hr": 120}],
        }
    ]

    result = process_triage_wards(wards, 10)

    assert result["acuity_score"] == 10
    assert result["status"] == "TRIAGE_STABLE"


def test_icu_standby_true():
    wards = [
        {
            "is_accepting": True,
            "icu_standby": True,
            "patients": [{"spo2": 98, "hr": 75}],
        }
    ]

    assert process_triage_wards(wards, 10)["acuity_score"] == 35


def test_icu_standby_false():
    wards = [
        {
            "is_accepting": True,
            "icu_standby": False,
            "patients": [{"spo2": 98, "hr": 75}],
        }
    ]

    assert process_triage_wards(wards, 10)["acuity_score"] == 10


def test_five_invalid_entries_trigger_ward_alert():
    patients = [{"spo2": 0, "hr": 75} for _ in range(5)]

    result = process_triage_wards(
        [{"is_accepting": True, "patients": patients}], 10
    )

    assert result["status"] == "WARD_ALERT"


def test_four_invalid_entries_do_not_trigger_ward_alert():
    patients = [{"spo2": 0, "hr": 75} for _ in range(4)]

    result = process_triage_wards(
        [{"is_accepting": True, "patients": patients}], 10
    )

    assert result["status"] == "NO_URGENT_CASES"


def test_zero_acuity_returns_no_urgent_cases():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 75}],
        }
    ]

    result = process_triage_wards(wards, 0)

    assert result == {
        "acuity_score": 0,
        "status": "NO_URGENT_CASES",
    }


def test_empty_sensor_streams_return_no_data():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"


def test_empty_manifold_returns_normal():
    assert monitor_oxygen_manifolds([[]]) == "PRESSURE_NORMAL"


def test_first_low_pressure_reading_does_not_fail():
    assert monitor_oxygen_manifolds([[3.9]]) == "PRESSURE_NORMAL"


def test_second_consecutive_low_reading_fails():
    assert monitor_oxygen_manifolds([[3.9, 3.8]]) == "PRESSURE_FAILURE"


def test_pressure_recovery_resets_streak():
    assert (
        monitor_oxygen_manifolds([[3.9, 4.0, 3.9]])
        == "PRESSURE_NORMAL"
    )


def test_low_readings_in_separate_manifolds_do_not_accumulate():
    assert (
        monitor_oxygen_manifolds([[3.9], [3.8]])
        == "PRESSURE_NORMAL"
    )
