def get_true_option(field_dict: dict) -> str | None:
    """
    Return key where value is True.
    """
    if not isinstance(field_dict, dict):
        return None

    for k, v in field_dict.items():
        if v is True:
            return k

    return None

def get_boolean_from_suffix(data: dict, base_key: str) -> bool:
    """
    Extract boolean flag from suffixed keys like *_Y.
    """
    return data.get(f"{base_key}_Y", False)
