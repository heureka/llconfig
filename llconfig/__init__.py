from collections import ChainMap, MutableMapping
import logging
import os
from pathlib import Path
import types

_logger = logging.getLogger(__name__)


class Config(MutableMapping):
    # TODO docstrings

    __slots__ = (
        'files', 'env_prefix', 'files_env_var', '_loaded', '_converters',
        '_override_layer', '_env_layer', '_file_layer', '_default_layer'
    )

    autoload = True

    file_glob_pattern = '*.cnf.py'

    def __init__(self, *files, env_prefix: str = 'APP_', files_env_var: str = 'CONFIG'):
        self.files = files
        self.env_prefix = env_prefix
        self.files_env_var = files_env_var
        self._loaded = False
        self._converters = {}

        self._override_layer = {}
        self._env_layer = {}
        self._file_layer = ChainMap()
        self._default_layer = {}

    def init(self, key: str, converter: callable, default=None):
        if key == self.files_env_var:
            raise KeyError('Conflict between directive name and `files_env_var` name.')

        self._loaded = False
        self._default_layer[key] = default
        self._converters[key] = converter

    def load(self):
        self._load_env_vars()
        self._load_files()
        self._loaded = True

    def _load_env_vars(self):
        _logger.debug('loading env vars')
        prefix = self.env_prefix
        self._env_layer = {
            key[len(prefix):]: val
            for key, val in os.environ.items()
            if key.startswith(prefix) and key[len(prefix):] in self._default_layer
        }
        _logger.info('env vars loaded')

    def _load_files(self):
        _logger.debug('loading files')

        paths = []

        if self.files_env_var:
            env_var = self.env_prefix + self.files_env_var
            _logger.debug('loading files from env var "{}"'.format(env_var))
            env_var_val = os.environ.get(env_var)
            if env_var_val:
                paths.extend(Path(p) for p in env_var_val.split(':'))

        if self.files:
            paths.extend(Path(p) for p in self.files)

        files = []
        for p in paths:
            if p.is_dir():
                files.extend(self._expand_dir(p))
            else:
                files.append(p)

        _logger.debug('list of files to load: {}'.format(files))
        self._file_layer.maps[:] = [self._load_file(f) for f in files]
        _logger.info('files loaded')

    def _expand_dir(self, path: Path):
        files = path.glob(self.file_glob_pattern)
        files = filter(lambda f: f.is_file(), files)
        files = sorted(files, key=lambda f: f.name, reverse=True)
        return files

    def _load_file(self, file: Path):
        _logger.debug('loading file: "{}"'.format(file))
        d = types.ModuleType(file.stem)
        d.__file__ = file.name
        exec(compile(file.read_bytes(), file.name, 'exec'), d.__dict__)
        return {key: getattr(d, key) for key in dir(d) if key in self._default_layer}

    # TODO naming?
    def get_namespace(self, namespace: str, lowercase: bool = True, trim_namespace: bool = True):
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

    def test(self):
        # TODO
        # _logger.debug('testing configuration')
        pass

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

        # 1. search in _override_layer
        if key in self._override_layer:
            return self._override_layer[key]

        # 2. search in _env_layer (and convert!)
        if key in self._env_layer:
            value = self._env_layer[key]
            try:
                return self._converters[key](value)
            except Exception as e:
                raise ValueError('Conversion error for key "{}".'.format(key)) from e

        # 3. search in _file_layer
        if key in self._file_layer:
            return self._file_layer[key]

        # 4. search (and possibly fail) in _default_layer
        return self._default_layer[key]

    def __setitem__(self, key: str, val):
        if key not in self._default_layer:
            raise KeyError('Overriding uninitialized key is prohibited.')

        self._override_layer[key] = val

    def __delitem__(self, key: str):
        del self._override_layer[key]

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, dict(self))
