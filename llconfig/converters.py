from json import loads as json_loads


def bool_like(val):
    return str(val).lower() not in ('false', '0', 'no', 'off', '')


def json(val):
    return json_loads(val, encoding='utf-8')
