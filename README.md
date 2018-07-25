llconfig
========

Lightweight layered configuration library.

All you need is Python >= 3.5 (and a keyboard).

------

## Basic concept

There is a `Config` object holding several layers of configuration keys and their values (= configuration directives).
From top to bottom:

1. Override layer = holds runtime directive overrides, if any.
2. Env layer = directives loaded from environment variables are kept in this layer, if any.
3. File layer = directives loaded from configuration file(s) are kept in this layer, if any.
4. Default layer = holds a default value for **every** initialized directive.

## Learn by example

The behavior is best shown on following example:

```python
from llconfig import Config

c = Config('local/override.cnf.py', '/etc/my_app/conf.d', env_prefix='MY_', config_files_env_var='CONFIG')
c.init('PORT', int, 80)
c.load()  # recommended, but not required (see docstrings)
c['PORT']
```

The returned value is `80`, given that there is no `MY_PORT` env
variable, no `MY_CONFIG` env variable and no `PORT = 1234` line in any of `local/override.cnf.py` or
`/etc/my_app/conf.d/*.cnf.py` configuration files.

### Search process

First, the override layer is searched, but there is no runtime override (no `c['PORT'] = 1234`) in this example.

The environment layer is searched next. If there is an env variable called `MY_PORT`, its value is taken
and **converted** using `int` function (this is necessary otherwise it wouldn't be possible to load anything
else than `str` from env variables).

Then, if the env variable is not present, the file layer is searched. There can be multiple files in this layer
(forming sub-layers) and all of them must be Python-executable. File sub-layers are processed in following order:

1. Files loaded from `MY_CONFIG` env variable. Its value is splitted using `:` (colon) as a delimiter and
   each part is handled the same way as if it would be passed to constructor (see bellow). The handling
   preserves order (so the leftmost part is always handled first).
2. Files passed to constructor (`local/override.cnf.py` and `/etc/my_app/conf.d` in this example). If there
   is a path pointing to directory instead of simple file, the **directory is expanded** (non-recursively). The
   expansion lists all files in given directory using `expansion_glob_pattern` attribute **sorted by file name
   in reverse order** (you can change this behavior by extending this class and overriding `_expand_dir`
   method). The expanded files are used as separate sub-layers in place of original directory.

When all of the file sub-layers are created, each configuration file **is executed** and each file's global
namespace is searched for the `PORT` directive (still preserving the order). If found, the directive is returned
as is (without conversion).

The default layer is searched as a last resort. As it contains values from directives' `init`, there is always a
default value (unless a search for non-initialized directive is performed). The default value is returned as is.

## Directive initialization

Directive is initialized using `init` method. It takes directive name, converter function (see bellow) and
a default value (which is `None` by default). It is recommended to name directives using upper-case only.
**Any directive you want to use must be initialized,** otherwise it is ignored (unknown env variables, unknown
directives in configuration files, etc.).

This means that once you initialize a directive you can safely use it without `KeyError`s or without calling
`c.get('PORT', 'default')`. There will always be at least the default value.

## Converters

Converters are arbitrary callables taking single `str` argument and returning anything. The converter is called
only for conversion from env variable. There are some predefined converters available in `llconfig.converters`,
but it is easy to create own. For example:

```python
from llconfig import Config
from llconfig.converters import json, bool_like
from pathlib import Path

c = Config()
c.init('PORT', int)  # "443" => 443
c.init('HOSTNAME', str)  # "localhost" => "localhost"
c.init('DEBUG', bool_like)  # "off" => False
c.init('DEBUG_2', bool)  # BEWARE: "0" => True 
c.init('FLEXIBLE', json)  # '{"hello": 1}' => {"hello": 1}
c.init('PICTURES', lambda raw: [Path(p) for p in raw.split(':')])  # "a.jpg:b.jpg" => [Path("a.jpg"), Path("b.jpg")]
```

Any exception raised during conversion is re-raised as a `ValueError`.

## Getting the values out

The `Config` object implements a mapping protocol, so you can use it as if it was a `dict`. In addition, there is a
`get_namespace` method [taken from Flask framework](http://flask.pocoo.org/docs/1.0/api/#flask.Config.get_namespace)
with exact same behavior (see their docs for more examples).

```python
from llconfig import Config

c = Config()
c.init('DB_HOST', str, 'localhost')
c.init('DB_PORT', int, 3306)
c.init('DB_USER', str)

c['DB_HOST']  # => 'localhost'
c['DB_USER']  # => None

c.get_namespace('DB_')  # => {'host': 'localhost', 'port': 3306, 'user': None}
c['DB_':]  # syntactic sugar - does the same as `c.get_namespace('DB_')`

dict(c)  # => {'DB_HOST': 'localhost', 'DB_PORT': 3306, 'DB_USER': None}
```

## Security

**In short: do not use this library in untrusted environment,** unless you completely understand how it works and
what possible attack vectors are. The main concern is that each file forming the file layer is executed. There
is also a possibility to load files using `config_files_env_var` environment variable (`APP_CONFIG` by default),
unless disabled. On top of that, you can compromise your application using badly written converter.