import json as _json


def bool_like(val):
    return str(val).lower() not in ('false', '0', 'no', 'off', 'disable', 'disabled', '')


def json(val):
    return _json.loads(val, encoding='utf-8')
