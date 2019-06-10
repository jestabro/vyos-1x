#!/usr/bin/python3

# Copyright 2019 VyOS maintainers and contributors <maintainers@vyos.io>
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
import os
import shlex
import subprocess
import tempfile
import vyos.defaults
import vyos.remote
import vyos.migrator
from vyos.config import Config
from vyos.configtree import ConfigTree

def to_escaped(a_string):
    return a_string.replace("\\", "\\\\")
def from_escaped(a_string):
    return a_string.replace("\\\\", "\\")

if (len(sys.argv) < 2):
    print("Need config file name to load.")
    print("Usage: load <config file>")
    sys.exit(0)

file_name = sys.argv[1]

configdir = vyos.defaults.directories['config']

protocols = ['scp', 'sftp', 'http', 'https', 'ftp', 'tftp']

if any(x in file_name for x in protocols):
    config_file = vyos.remote.get_remote_config(file_name)
    if not config_file:
        sys.exit("No config file by that name.")
else:
    canonical_path = "{0}/{1}".format(configdir, file_name)
    first_err = None
    try:
        with open(canonical_path, 'r') as f:
            config_file = f.read()
    except Exception as err:
        first_err = err
        try:
            with open(file_name, 'r') as f:
                config_file = f.read()
        except Exception as err:
            print(first_err)
            print(err)
            sys.exit(1)

with tempfile.NamedTemporaryFile() as file_to_migrate:
    with open(file_to_migrate.name, 'w') as fd:
        fd.write(config_file)

    migration = vyos.migrator.Migrator(file_to_migrate.name)
    migration.run()
    if migration.config_changed():
        with open(file_to_migrate.name, 'r') as fd:
            config_file = fd.read()

# escape any backslashes in values, before passing to ConfigTree; cf.
# T1001.
config_file = to_escaped(config_file)
load_config_tree = ConfigTree(config_file)

effective_config = Config()

# showConfig (called by config.show_config() does not escape
# backslashes.
output_effective_config = effective_config.show_config()
output_effective_config = to_escaped(output_effective_config)
effective_config_tree = ConfigTree(output_effective_config)

effective_cmds = effective_config_tree.to_commands()
load_cmds = load_config_tree.to_commands()

effective_cmd_list = effective_cmds.splitlines()
load_cmd_list =  load_cmds.splitlines()

# splitlines() escapes backslashes, which is redundant due to
# to_escaped, above.
effective_cmd_list = [ from_escaped(cmd) for cmd in effective_cmd_list ]
load_cmd_list = [ from_escaped(cmd) for cmd in load_cmd_list ]

effective_cmd_set = set(effective_cmd_list)
load_cmd_set = set(load_cmd_list)

remove_cmd_list = [ cmd for cmd
        in effective_cmd_list if cmd not in load_cmd_set ]
load_cmd_list = [ cmd for cmd
        in load_cmd_list if cmd not in effective_cmd_set ]

prune_cmd_list = []

# This is a workaround to find a minimal set of 'delete' commands
# to pass to the cli-shell-api backend; it is unsatisfying, but
# mercifully terse.
remove_cmd = ''
for cmd in remove_cmd_list:
    if remove_cmd and remove_cmd in cmd:
        continue
    while cmd > 'set' and cmd not in load_cmds:
        prune_cmd = cmd
        tmp = shlex.split(cmd, posix=False)
        cmd = ' '.join(tmp[:-1])

    remove_cmd = prune_cmd

    prune_cmd_list.append(prune_cmd)

delete_cmd_list = [ cmd.replace('set', 'delete', 1) for cmd
        in prune_cmd_list ]

for cmd in delete_cmd_list:
    cmd = "/opt/vyatta/sbin/my_" + cmd

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print("Called process error: {}.".format(err))

for cmd in load_cmd_list:
    cmd = "/opt/vyatta/sbin/my_" + cmd

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as err:
        print("Called process error: {}.".format(err))

if effective_config.session_changed():
    print("Load complete. Use 'commit' to make changes effective.")
else:
    print("No configuration changes to commit.")
