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
import os
import time

from vyos.config import Config
from vyos.configdict import list_diff
from vyos import ConfigError
from vyos.base import Warning
from vyos.utils.dict import dict_search

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()

    base = 'simple'
    if not conf.exists(base):
        return None

    d = conf.get_config_dict(base, get_first_key=True)

    print(f"JSE dict: {d}")

    return d

def verify(c):
    if dict_search("some-tag-node.some1", c) is not None:
        Warning("JSE this is a warning")

    if dict_search("some-tag-node.some2", c) is not None:
        raise ConfigError('JSE this is a ConfigError')

    return None

def generate(c):
    return None

def apply(c):
#    time.sleep(42)
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

