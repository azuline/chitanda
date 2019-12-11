import pytest
from mock import Mock, patch

from chitanda.loader import (
    _get_module_names,
    _is_module_enabled,
    load_commands,
)


@patch('chitanda.loader.importlib')
@patch('chitanda.loader.sys')
@patch('chitanda.loader._is_module_enabled')
@patch('chitanda.loader._get_module_names')
def test_load_commands(get_module_names, is_module_enabled, sys, importlib):
    get_module_names.return_value = ['chii.a', 'chii.b', 'chii.c', 'chii.d']
    is_module_enabled.side_effect = [True, True, False, False]
    sys.modules = {'chii.b': 456, 'chii.d': Mock()}

    load_commands(123, run_setup=False)
    assert 'chii.d' not in sys.modules
    importlib.reload.assert_called_with(456)
    importlib.import_module.assert_called_with('chii.a')


@patch('chitanda.loader.importlib')
@patch('chitanda.loader.sys')
@patch('chitanda.loader._is_module_enabled')
@patch('chitanda.loader._get_module_names')
def test_run_setup(get_module_names, is_module_enabled, sys, importlib):
    get_module_names.return_value = ['chii.a', 'chii.b']
    is_module_enabled.side_effect = [True, True]
    chii_b = Mock()
    sys.modules = {'chii.a': None, 'chii.b': chii_b}

    load_commands(123, run_setup=True)
    assert chii_b.setup.called_with(123)


@pytest.mark.parametrize(
    'full_name, enabled',
    [('chitanda.modules.a', True), ('chitanda.modules.e', False)],
)
def test_is_module_enabled(full_name, enabled, monkeypatch):
    monkeypatch.setattr(
        'chitanda.loader.config', {'modules': {'global': ['a', 'b', 'c']}}
    )
    assert _is_module_enabled(full_name) is enabled


def test_get_module_names():
    module_names = _get_module_names()
    assert 'chitanda.modules.quotes.add' in module_names
    assert 'chitanda.modules.sed' in module_names
