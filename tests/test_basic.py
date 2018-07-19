from llconfig import Config


def test_basic():
    c = Config()

    c.init('HOST', str, '0.0.0.0')
    c.init('PORT', int, 8080)

    assert c['HOST'] == '0.0.0.0'
    assert c['PORT'] == 8080
