def assert_enum_value(obj, attr, expected):
    """Checks that model.<field>.value == expected."""
    val = getattr(obj, attr)
    if hasattr(val, "value"):
        assert val.value == expected
    else:
        assert val == expected
