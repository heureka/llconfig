from llconfig import Config


def test_basic():
    c = Config(env_prefix='VIRTUAL_')
    c.init('HOST', str, '0.0.0.0')
    c.init('PORT', int, 8080)
    c.load()

    assert c['HOST'] == '0.0.0.0'
    assert c['PORT'] == 8080
