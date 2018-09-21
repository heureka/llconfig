import contextlib
import os

from llconfig import Config


@contextlib.contextmanager
def env(**kwargs):
    original = {key: os.getenv(key) for key in kwargs}
    os.environ.update({key: str(value) for key, value in kwargs.items()})
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


def test_prefixed_variables_override():
    c = Config(env_prefix='PREFIX_')
    c.init('HOST', str, '0.0.0.0')
    with env(PREFIX_HOST='1.2.3.4'):
        c.load()

    assert c['HOST'] == '1.2.3.4'


def test_nonprefixed_variables_override_empty_prefix():
    c = Config(env_prefix='')
    c.init('HOST', str, '0.0.0.0')
    with env(HOST='1.2.3.4'):
        c.load()

    assert c['HOST'] == '1.2.3.4'


def test_nonprefixed_variables_dont_override_nonempty_prefix():
    c = Config(env_prefix='PREFIX_')
    c.init('HOST', str, '0.0.0.0')
    with env(HOST='1.2.3.4'):
        c.load()

    assert c['HOST'] == '0.0.0.0'


def test_int_from_environ():
    c = Config(env_prefix='PREFIX_')
    c.init('NUM', int, 42)
    with env(PREFIX_NUM='42'):
        c.load()

    assert c['NUM'] == 42
