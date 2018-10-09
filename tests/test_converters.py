from decimal import Decimal

import pytest

from llconfig import Config
from llconfig.converters import bool_like, json
from tests import env


@pytest.mark.parametrize('_type', [int, float, complex, Decimal])
def test_python_numeric_types_converters(_type):
    c = Config(env_prefix='')
    c.init('VALUE', _type)
    with env(VALUE='1'):
        c.load()

    assert c['VALUE'] == _type('1')
    assert c['VALUE'] == 1
    assert type(c['VALUE']) == _type


@pytest.mark.parametrize('value', ['0', 'no', 'disabled', 'False', 'enabled'])
def test_python_bool_type(value):
    c = Config(env_prefix='')
    with pytest.warns(UserWarning):
        c.init('VALUE', bool)
    with env(VALUE=value):
        c.load()

    assert c['VALUE'] is True


@pytest.mark.parametrize('value', ['0', 'NO', 'disabled', 'Off', 'false'])
def test_bool_like_false(value):
    c = Config(env_prefix='')
    c.init('VALUE', bool_like)
    with env(VALUE=value):
        c.load()

    assert c['VALUE'] is False


@pytest.mark.parametrize('value', ['1', 'YES', 'enabled', 'True', 'on'])
def test_bool_like_true(value):
    c = Config(env_prefix='')
    c.init('VALUE', bool_like)
    with env(VALUE=value):
        c.load()

    assert c['VALUE'] is True


def test_json():
    c = Config(env_prefix='')
    c.init('VALUE1', json)
    c.init('VALUE2', json)
    with env(VALUE1='{"aha": [1, 1.2, false]}', VALUE2='1'):
        c.load()

    assert c['VALUE1'] == {'aha': [1, 1.2, False]}
    assert c['VALUE2'] == 1


def test_custom_converter():
    def custom(value):
        return ...

    c = Config(env_prefix='')
    c.init('VALUE', custom)
    with env(VALUE='42'):
        c.load()
    assert c['VALUE'] is ...


def test_custom_anonymous_converter():
    c = Config(env_prefix='')
    c.init('VALUE', lambda x: ...)
    with env(VALUE='42'):
        c.load()
    assert c['VALUE'] is ...
