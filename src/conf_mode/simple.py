#!/usr/bin/env python3
#
# Copyright (C) 2019-2020 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from vyos.config import Config
from vyos import ConfigError

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()

    base = 'simple'
    if not conf.exists(base):
        return None

    d = conf.get_config_dict(base, get_first_key=True)

#    print(f"JSE dict: {d}")

    return d

def verify(c):
    if not c:
        return None

    sub = c.get('some-tag-node', {})
    if 'some777' in sub and 'some778' not in sub:
        raise ConfigError('this is a verify error')

    return None

def generate(_c):
    return None

def apply(c):
    if not c:
        return None

    sub = c.get('some-tag-node', {})
    if 'some666' in sub:
        raise ConfigError('this is an apply error')

    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        sys.exit(1)
