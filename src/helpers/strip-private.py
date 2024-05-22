#!/usr/bin/python3

# Copyright 2021-2024 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import sys
import json
import shlex

from vyos.configtree import ConfigTree
from vyos.utils.dict import dict_to_paths
from vyos.xml_ref import is_secret_value


def anonymize_data(_v):
    return "<DATA REDACTED>"

def strip_private_tree(config_tree: ConfigTree):
    json_data = config_tree.to_json()
    dict_data = json.loads(json_data)
    for p in dict_to_paths(dict_data):
        if is_secret_value(p):
            config_tree.set(p[:-1], value=anonymize_data(p[-1]), replace=True)

    return config_tree.to_string()

def strip_private_commands(config_cmds: str):
    commands = config_cmds.splitlines()
    for i, cmd in enumerate(commands):
        cmd = shlex.split(cmd)
        if is_secret_value(cmd[1:]):
            cmd = cmd[:-1] + [anonymize_data(cmd[-1])]
            commands[i] = ' '.join(cmd)

    return '\n'.join(commands)

def strip_private(config_source):
    try:
        config_tree = ConfigTree(config_source)
    except ValueError:
        pass
    else:
        return strip_private_tree(config_tree)

    return strip_private_commands(config_source)

def read_input():
    try:
        return sys.stdin.read()
    # stdin can be cut for any reason, such as user interrupt or the pager terminating before the text can be read.
    # All we can do is gracefully exit.
    except (BrokenPipeError, EOFError, KeyboardInterrupt):
        sys.exit(1)

if __name__ == "__main__":
    config_source = read_input()
    stripped_config = strip_private(config_source)
    print(stripped_config)
