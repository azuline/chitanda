import importlib
import itertools
import sys
from pkgutil import iter_modules

import chitanda.modules  # noqa
from chitanda.config import config
from chitanda.util import get_module_name


def load_commands(bot, run_setup=True):
    for name in _get_module_names():
        if not _is_module_enabled(name):
            if name in sys.modules:
                del sys.modules[name]
        else:
            if name in sys.modules:
                importlib.reload(sys.modules[name])
            else:
                importlib.import_module(name)

            if run_setup and hasattr(sys.modules[name], 'setup'):
                sys.modules[name].setup(bot)


def _is_module_enabled(full_name):
    name = get_module_name(full_name)
    return name in _get_all_enabled_modules()


def _get_module_names(pkg_path='chitanda.modules'):
    for module_info in iter_modules(sys.modules[pkg_path].__path__):
        name = f'{pkg_path}.{module_info.name}'
        if module_info.ispkg:
            importlib.import_module(name)
            for name_ in _get_module_names(name):
                yield name_
        yield name


def _get_all_enabled_modules():
    return list(set(itertools.chain.from_iterable(config['modules'].values())))
