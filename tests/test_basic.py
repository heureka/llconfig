import pytest

from llconfig import Config


def test_basic():
    c = Config()
    c.init('HOST', str, '0.0.0.0')
    c.init('PORT', int, 8080)
    c.load()

    assert c['HOST'] == '0.0.0.0'
    assert c['PORT'] == 8080


def test_case_sensitivity():
    c = Config()
    c.init('TEST', str, 'TEST')
    with pytest.warns(UserWarning):
        c.init('test', str, 'test')
    c.load()

    assert c['TEST'] == 'TEST'
    assert c['test'] == 'test'


def test_basic_values_work_without_load():
    c = Config()
    c.init('TEST', str, 'TEST')
    # no load!

    assert c['TEST'] == 'TEST'


def test_nonexisting_config_is_missing():
    c = Config()
    c.init('TEST', str, 'TEST')
    c.load()

    assert 'TEST' in c
    assert 'NOMNOMNOM' not in c

    with pytest.raises(KeyError):
        c['NOMNOMNOM']


def test_properties():
    c = Config()
    c.init('TEST', str, 'TEST')
    c.load()

    assert c.test == 'TEST'
