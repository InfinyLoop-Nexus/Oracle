def assert_dictionaries_are_equal_except(dict1: dict, dict2: dict, excluded_keys: list[str]) -> bool:
    """
    Checks if two dictionaries are equal, excluding specified keys.

    Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.
        excluded_keys (list[str]): A list of keys to exclude from the comparison.

    Returns:
        bool: True if the dictionaries are equal (excluding the specified keys), False otherwise.
    """
    d1 = {k: v for k, v in dict1.items() if k not in excluded_keys}
    d2 = {k: v for k, v in dict2.items() if k not in excluded_keys}
    assert d1 == d2