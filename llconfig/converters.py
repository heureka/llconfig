import json as _json


def bool_like(val):
    return str(val).lower() not in ('false', '0', 'no', 'off', 'disable', 'disabled', '')


def json(val):
    """
    A convenient converter that JSON-deserializes strings or checks if Python
    object is JSON-serializable.
    """
    if isinstance(val, str):
        return _json.loads(val, encoding='utf-8')
    else:
        _json.dumps(val)
        return val
