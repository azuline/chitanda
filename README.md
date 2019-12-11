# chitanda

[![Build Status](https://travis-ci.org/azuline/chitanda.svg?branch=master)](https://travis-ci.org/azuline/chitanda)
[![Coverage Status](https://coveralls.io/repos/github/azuline/chitanda/badge.svg?branch=master)](https://coveralls.io/github/azuline/chitanda?branch=master)
[![Pypi](https://img.shields.io/pypi/v/chitanda.svg)](https://pypi.python.org/pypi/chitanda)
[![Pyversions](https://img.shields.io/pypi/pyversions/chitanda.svg)](https://pypi.python.org/pypi/chitanda)
[![Documentation Status](https://readthedocs.org/projects/chitanda/badge/?version=latest)](https://chitanda.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

An extensible IRC & Discord bot. Requires Python 3.7.

Read the documentation at https://chitanda.readthedocs.io.

## Quickstart

It is recommended that chitanda be installed with `pipx`; however, if that is
not possible, `pip install --user` will also work.

```bash
$ pipx install chitanda
$ chitanda migrate  # Upgrade database to latest version.
$ chitanda config  # See wiki for configuration instructions.
$ chitanda run
```

## License

```
Copyright (C) 2019 azuline <azuline@riseup.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```
