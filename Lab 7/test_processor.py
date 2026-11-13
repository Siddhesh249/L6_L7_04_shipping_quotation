from hypothesis import given, strategies as st
from processor import calculate_dimensional_weight, format_tracking_label, parse_package_manifest

@given(st.text() | st.none())
def test_calculate_dimensional_weight_no_crash(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_format_tracking_label_safe(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_parse_package_manifest_safe(s):
    #To-Do:Using try and except complete this function.
    pass