import pytest
from decimal import Decimal

from llconfig import Config
from llconfig.converters import bool_like, json


@pytest.mark.parametrize('_type', [int, float, complex, Decimal])
def test_python_numeric_types_converters(_type):
    c = Config()
    c.init('VALUE', _type, '1')
    c.load()

    assert c['VALUE'] == _type('1')
    assert c['VALUE'] == 1
    assert type(c['VALUE']) == _type


@pytest.mark.parametrize('value', ['0', 'no', 'disabled', 'False', 'enabled'])
def test_python_bool_type(value):
    c = Config()
    with pytest.warns(UserWarning):
        c.init('VALUE', bool, value)
    c.load()

    assert c['VALUE'] is True


@pytest.mark.parametrize('value', ['0', 'NO', 'disabled', 'Off', 'false'])
def test_bool_like_false(value):
    c = Config()
    c.init('VALUE', bool_like, value)
    c.load()

    assert c['VALUE'] is False


@pytest.mark.parametrize('value', ['1', 'YES', 'enabled', 'True', 'on'])
def test_bool_like_true(value):
    c = Config()
    c.init('VALUE', bool_like, value)
    c.load()

    assert c['VALUE'] is True


def test_json():
    c = Config()
    c.init('VALUE1', json, '{"aha": [1, 1.2, false]}')
    c.init('VALUE2', json, 1)
    with pytest.raises(TypeError):
        c.init('VALUE3', json, set())
    c.load()

    assert c['VALUE1'] == {'aha': [1, 1.2, False]}
    assert c['VALUE2'] == 1


def test_custom_converter():
    def custom(value):
        return ...

    c = Config()
    c.init('VALUE', custom, 42)
    c.load()
    assert c['VALUE'] == ...


def test_custom_anonymous_converter():
    c = Config()
    c.init('VALUE', lambda x: ..., 42)
    c.load()
    assert c['VALUE'] == ...
