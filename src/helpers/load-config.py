#!/usr/bin/env python3

import sys

from pathlib import Path
from gzip import open as zopen
from argparse import ArgumentParser

from vyos.config import Config
from vyos.configtree import ConfigTree, DiffTree
from vyos.utils.process import cmd, DEVNULL

def get_arguments():
    """Get arguments from command line."""
    parser = ArgumentParser(description='Load a config from stdin or file.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', '-f',
                       help='Load proposed config from path.')
    group.add_argument('--stdin', '-i', action='store_true',
                       help='Load proposed config from stdin.')
    group.add_argument('--rollback', '-r', type=int,
                       help='Rollback a number of commits')
    group.add_argument('--saved', '-s', action='store_true',
                       help='Load saved startup configuration')
    return vars(parser.parse_args())

def sanitize_config(ctree: ConfigTree):
    path = ['interfaces', 'ethernet']
    for interface in ctree.list_nodes(path):
        hw_id = path + [interface, 'hw-id']
        if ctree.exists(hw_id):
            ctree.delete(hw_id)

def read_proposed_config():
    """Load a config from stdin."""
    proposed_str = sys.stdin.read()
    return proposed_str

def get_running_config(config: Config) -> ConfigTree:
    return config.get_config_tree(effective=False)

def get_proposed_config(file: str = None) -> ConfigTree:
    if file is None:
        config_str = read_proposed_config()
    elif file.endswith('.gz'):
        config_str = zopen(file, 'r').read().decode()
    else:
        config_str = Path(file).read_text()
    return ConfigTree(config_str)

def calculate_diff(ctree: ConfigTree, ntree: ConfigTree) -> list:
    """Calculate the diff between the current and proposed config."""
    # Sanitize the config trees
    sanitize_config(ctree)
    sanitize_config(ntree)
    # Calculate the diff between the current and new config tree
    commands = DiffTree(ctree, ntree).to_commands()
    # on an empty set of 'add' or 'delete' commands, to_commands
    # returns '\n'; prune below
    command_list = commands.splitlines()
    command_list = [c for c in command_list if c]
    return command_list

def set_commands(cmds: list) -> None:
    """Set commands in the config session."""
    if not cmds:
        print('no commands to set')
        return
    for op in cmds:
        try:
            cmd(f'/opt/vyatta/sbin/my_{op}', shell=True, stderr=DEVNULL)
        except OSError as e:
            print(e)
            continue

def run():
    """Load a config from stdin or file."""
    args = get_arguments()
    config = Config()
    if not config.in_session():
        print('not in config session; if you want to run anywhere, contact author')
        return
    if args['file']:
        file = args['file']
    elif args['rollback']:
        file = f'/opt/vyatta/etc/config/archive/config.boot.{args["rollback"]}.gz'
    elif args['saved']:
        file = '/opt/vyatta/etc/config/config.boot'
    else:
        file = None
    # Get the current and proposed config trees
    ctree = get_running_config(config)
    ntree = get_proposed_config(file)
    # Calculate the diff between the current and proposed config
    cmds = calculate_diff(ctree, ntree)
    # Set the commands in the config session
    set_commands(cmds)

if __name__ == '__main__':
    run()
