"""
Copyright (c) 2021 Heureka Group a.s. All Rights Reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from collections import ChainMap
from collections.abc import MutableMapping
import logging
import os
from pathlib import Path
import string
import types
from typing import Optional, Union, Any, Callable
import warnings

_logger = logging.getLogger(__name__)


class Config(MutableMapping):
    """
    Main object holding the configuration.
    """

    __slots__ = (
        'config_files', 'env_prefix', 'config_files_env_var', '_loaded', '_converters',
        '_override_layer', '_env_layer', '_file_layer', '_default_layer'
    )

    autoload = True
    """bool: Whether to automatically trigger load() on item access or configuration test (if not loaded yet)."""

    expansion_glob_pattern = '*.cnf.py'
    """str: Pattern used to expand a directory, when passed instead of a config file."""

    def __init__(
            self,
            *config_files: Union[str, Path],
            env_prefix: str = 'APP_',
            config_files_env_var: Optional[str] = 'CONFIG'
    ):
        """
        Create configuration object, init empty layers.

        Args:
            *config_files: Configuration files to load to the file layer.
            env_prefix: Prefix of all env vars handled by this library (set to empty string to disable prefixing).
            config_files_env_var: Name of env var containing colon delimited list of files to prepend to `config_files`.
                Set to `None` to disable this behavior.
        """
        _check_safe_env_name(env_prefix)
        _check_safe_env_name(config_files_env_var)

        self.config_files = config_files
        self.env_prefix = env_prefix
        self.config_files_env_var = config_files_env_var
        self._loaded = False

        self._converters = {}
        """Holds converter functions to be called every time when converting env variable."""

        self._override_layer = {}
        """Layer holding runtime directive overrides, if any."""

        self._env_layer = {}
        """Layer holding directives loaded from environment variables, if any."""

        self._file_layer = ChainMap()
        """Layer holding directives loaded from file(s), if any."""

        self._default_layer = {}
        """Layer holding default value for every initialized directive."""

    def init(self, key: str, converter: Callable[[str], Any], default=None):
        """
        Initialize configuration directive.

        Args:
            key: Case-sensitive directive name which is used everywhere (in env vars, in config files, in defaults).
            converter: Function, which is called when converting env variable value to Python.
            default: Directive default value.
        """
        if key == self.config_files_env_var:
            raise KeyError('Conflict between directive name and `config_files_env_var` name.')

        _check_safe_env_name(key)

        self._loaded = False
        self._default_layer[key] = default
        self._converters[key] = converter

        if converter == bool:
            warnings.warn('Using bool as converter is unsafe as it will treat all nonempty strings as True. '
                          'Use llconfig.converters.bool_like converter instead.', stacklevel=3)

    def load(self):
        """
        Load env layer and file layer.

        There is no need to call this explicitly when `autoload` is turned on, but it may be useful to trigger
        possible env vars conversion errors as soon as possible.

        Raises:
             ValueError: When conversion fails for any of env vars.
        """
        self._load_env_vars()
        self._load_files()
        self._loaded = True

    def _load_env_vars(self):
        _logger.debug('loading env vars')
        for prefixed_key, value in os.environ.items():
            if not prefixed_key.startswith(self.env_prefix):
                continue
            key = prefixed_key[len(self.env_prefix):]
            if key not in self._default_layer:
                continue
            try:
                self._env_layer[key] = self._converters[key](value)
            except Exception as e:
                raise ValueError('Conversion error for environment variable "{}".'.format(self.env_prefix + key)) from e
        _logger.info('env vars loaded')

    def _load_files(self):
        _logger.debug('loading config files')

        paths = []

        if self.config_files_env_var:
            env_var = self.env_prefix + self.config_files_env_var
            _logger.debug('getting list of config files from env var "{}"'.format(env_var))
            env_var_val = os.environ.get(env_var)
            if env_var_val:
                paths.extend(Path(p) for p in env_var_val.split(':'))

        if self.config_files:
            paths.extend(Path(p) for p in self.config_files)

        config_files = []
        for p in paths:
            if p.is_dir():
                config_files.extend(self._expand_dir(p))
            else:
                config_files.append(p)

        _logger.debug('list of config files to load: {}'.format(config_files))
        self._file_layer.maps[:] = [self._load_file(f) for f in config_files]
        _logger.info('config files loaded')

    def _expand_dir(self, path: Path):
        """
        Returns:
            List[Path]: Contents of given path non-recursively expanded using `expansion_glob_pattern`, sorted by file
                name in reverse order.
        """
        files = path.glob(self.expansion_glob_pattern)
        files = filter(lambda f: f.is_file(), files)
        files = sorted(files, key=lambda f: f.name, reverse=True)
        return list(files)

    def _load_file(self, file: Path):
        """
        Execute given file and parse config directives from it.

        Returns:
            Dict[str, Any]: Global namespace of executed file filtered to contain only initialized config keys.
        """
        _logger.debug('loading file: "{}"'.format(file))
        d = types.ModuleType(file.stem)
        d.__file__ = file.name
        exec(compile(file.read_bytes(), file.name, 'exec'), d.__dict__)
        return {key: getattr(d, key) for key in dir(d) if key in self._default_layer}

    def get_namespace(self, namespace: str, lowercase: bool = True, trim_namespace: bool = True):
        """
        Returns:
            Dict[str, Any]: Dict containing a subset of configuration options matching the specified namespace.

        See Also:
            http://flask.pocoo.org/docs/1.0/api/#flask.Config.get_namespace
        """
        if not namespace:
            raise ValueError('Namespace must not be empty.')

        res = {}
        for k, v in self.items():
            if not k.startswith(namespace):
                continue
            if trim_namespace:
                key = k[len(namespace):]
            else:
                key = k
            if lowercase:
                key = key.lower()
            res[key] = v

        return res

    def __len__(self):
        return len(self._default_layer)

    def __iter__(self):
        return iter(self._default_layer)

    def __getitem__(self, key):
        if not self._loaded and self.autoload:
            self.load()

        # add a bit of syntactic sugar
        if isinstance(key, slice):
            return self.get_namespace(key.start)

        if key in self._override_layer:
            return self._override_layer[key]

        if key in self._env_layer:
            return self._env_layer[key]

        if key in self._file_layer:
            return self._file_layer[key]

        # search in _default_layer is intended to possibly fail
        return self._default_layer[key]

    def __setitem__(self, key: str, val):
        if key not in self._default_layer:
            raise KeyError('Overriding uninitialized key is prohibited.')

        self._override_layer[key] = val

    def __delitem__(self, key: str):
        del self._override_layer[key]

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, dict(self))


# https://stackoverflow.com/a/2821183/570503
_ENV_SAFE_CHARSET = set(string.ascii_uppercase + string.digits + '_')
"""Set[str]: Set of characters considered to be safe for environment variable names."""


def _check_safe_env_name(name, stacklevel=3):  # this function => Config object => caller of Config object == 3 levels
    if not all(ch in _ENV_SAFE_CHARSET for ch in name):
        warnings.warn('Name "{}" is unsafe for use in environment variables.'.format(name), stacklevel=stacklevel)
