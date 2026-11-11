
import pytest
import math
from hypothesis import given, settings, strategies as st

from processor import process_triage_wards, monitor_oxygen_manifolds


# --------------------------------------------------
# FUNCTION 1: process_triage_wards()
# --------------------------------------------------

# Test 1: Invalid wards input
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.booleans(),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_wards_input(wards):
    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# Test 2: Invalid default acuity score
@given(st.one_of(
    st.none(),
    st.text(),
    st.booleans(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_default_acuity(score):
    with pytest.raises(ValueError):
        process_triage_wards([], score)


# Test 3: Invalid ward entries
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.booleans(),
    st.lists(st.integers())
))
def test_invalid_ward_entry(ward):
    with pytest.raises(ValueError):
        process_triage_wards([ward], 10)


# Test 4: Invalid patients collection
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.booleans(),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_patients_collection(patients):
    wards = [{
        "is_accepting": True,
        "patients": patients
    }]

    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# Test 5: Invalid patient entries
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.booleans(),
    st.lists(st.integers())
))
def test_invalid_patient_entry(patient):
    wards = [{
        "is_accepting": True,
        "patients": [patient]
    }]

    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# Test 6: Invalid oxygen saturation
@given(st.one_of(
    st.none(),
    st.text(),
    st.booleans(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_spo2(spo2):
    wards = [{
        "is_accepting": True,
        "patients": [{"spo2": spo2, "hr": 75}]
    }]

    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# Test 7: Invalid heart rate
@given(st.one_of(
    st.none(),
    st.text(),
    st.booleans(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_heart_rate(hr):
    wards = [{
        "is_accepting": True,
        "patients": [{"spo2": 98, "hr": hr}]
    }]

    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# Test 8: Invalid consciousness indicator
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_unconscious_value(value):
    wards = [{
        "is_accepting": True,
        "patients": [{
            "spo2": 98,
            "hr": 75,
            "unconscious": value
        }]
    }]

    with pytest.raises(ValueError):
        process_triage_wards(wards, 10)


# --------------------------------------------------
# FUNCTION 2: monitor_oxygen_manifolds()
# --------------------------------------------------

# Test 9: Invalid sensor stream input
@given(st.one_of(
    st.integers(min_value=1),
    st.text(min_size=1),
    st.booleans(),
    st.dictionaries(st.text(), st.integers(), min_size=1)
))
def test_invalid_sensor_streams(streams):
    with pytest.raises(ValueError):
        monitor_oxygen_manifolds(streams)


# Test 10: Invalid manifold entries
@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.booleans(),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_manifold(manifold):
    with pytest.raises(ValueError):
        monitor_oxygen_manifolds([manifold])


# Test 11: Invalid pressure readings
@given(st.one_of(
    st.none(),
    st.text(),
    st.booleans(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_pressure_reading(pressure):
    with pytest.raises(ValueError):
        monitor_oxygen_manifolds([[pressure]])


# Test 12: Non-finite pressure values
@given(st.sampled_from([
    float("nan"),
    float("inf"),
    float("-inf")
]))
def test_non_finite_pressure(pressure):
    with pytest.raises(ValueError):
        monitor_oxygen_manifolds([[pressure]])


# --------------------------------------------------
# VALID INPUT TESTS
# --------------------------------------------------

def test_empty_wards():
    result = process_triage_wards([], 10)

    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_normal_oxygen_pressure():
    assert monitor_oxygen_manifolds([[4.5, 4.2]]) == "PRESSURE_NORMAL"


def test_two_consecutive_low_pressures():
    assert monitor_oxygen_manifolds([[3.5, 3.8]]) == "PRESSURE_FAILURE"


def test_single_low_pressure():
    assert monitor_oxygen_manifolds([[3.5, 4.2]]) == "PRESSURE_NORMAL"
