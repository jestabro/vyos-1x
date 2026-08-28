# Copyright (C) VyOS Inc.
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

"""
simple POC of an interactive apply-path

To use as post-commit script:
ln -s /usr/bin/apply-path /etc/commit/post-hooks.d/17vyos-apply-path-check
"""

import os
import sys
import typing
from dataclasses import dataclass
from dataclasses import field
from functools import reduce

from vyos.referencetree import ReferenceTree
from vyos.configtree import subtree_values_of_path
from vyos.configtree import ConfigTreeError
from vyos.configsource import ConfigSourceSession
from vyos.configsession import ConfigSession
from vyos.config import Config
from vyos.utils.func import FalseCallable


@dataclass
class PathData:
    source: list[str] = field(default_factory=list)
    target: list[str] = field(default_factory=list)
    translate: typing.Callable = FalseCallable()


test_data = PathData(
    source=['protocols', 'static', 'route'],
    target=['firewall', 'group', 'network-group', 'smoketest_derived', 'network'],
)


def check_session(strict: bool) -> None:
    """Check if we are in a config session, with no uncommitted changes, if
    strict.
    """
    context = ConfigSourceSession()

    if not context.in_session():
        print('Run from within a config session')
        sys.exit()

    if strict and context.session_changed():
        print('There are uncommitted changes: commit or discard before running')
        sys.exit()


class ApplyPathError(Exception):
    pass


class ApplyPath:
    def __init__(self):
        self.session = ConfigSession(os.getppid(), shared=True)
        env = self.session.get_session_env()
        config = Config(session_env=env)

        self.rt = ReferenceTree()
        self.ct = config._session_config

        self.path_data: list[PathData] = [test_data]

    def get_source_values(self, data) -> list[str]:
        source_tuples = subtree_values_of_path(self.ct, data.source, self.rt)
        source_values = reduce(
            lambda acc, x: list(set(acc) | set(x[0])), source_tuples, []
        )
        source_values = (
            data.translate(source_values) if data.translate else source_values
        )

        return source_values

    def get_target_tuple(self, data) -> tuple[list[str], list[str]] | None:
        # pylint: disable=redefined-outer-name
        try:
            target_tuples = subtree_values_of_path(self.ct, data.target, self.rt)
        except ConfigTreeError as e:
            print(e)
            return None

        if not target_tuples or not target_tuples[0][1]:
            # path does not yet exist in config tree
            # suggested to add viability check here, but this is just a POC
            return ([], data.target)

        if len(target_tuples) > 1:
            paths = [p for (_, p) in target_tuples]
            print(f'Target path is not well defined: {data.target} !')
            print(f'Wildcard gives possible paths: {paths}')
            print('Wildcard allowed in source, not target.')
            return None

        return target_tuples[0]

    def check_path(self, data: PathData):
        target_tuple = self.get_target_tuple(data)
        if target_tuple is None:
            return

        target_values = target_tuple[0]
        source_values = self.get_source_values(data)

        if set(target_values) != set(source_values):
            print(
                f'Entries of target path: {data.target} out of sync with those of source path: {data.source}'
            )
            print('See "apply-path -h"')

    def check(self):
        for data in self.path_data:
            self.check_path(data)

        return '', 0

    def update_path(self, data: PathData):
        target_tuple = self.get_target_tuple(data)
        if target_tuple is None:
            return

        target_values = target_tuple[0]
        target_path = target_tuple[1]
        source_values = self.get_source_values(data)

        if set(target_values) != set(source_values):
            for value in sorted(list(set(target_values) - set(source_values))):
                self.session.delete(target_path, value=value)
            for value in sorted(list(set(source_values) - set(target_values))):
                self.session.set(target_path, value=value)

    def update(self):
        for data in self.path_data:
            self.update_path(data)

        return '', 0


# entry_point for console script
#
def run():
    # pylint: disable=broad-exception-caught,import-outside-toplevel
    from argparse import ArgumentParser

    check_session(strict=True)

    check_name = 'check'
    update_name = 'update'

    apply_path = ApplyPath()

    if sys.argv[0].replace('-', '_').endswith('apply_path_' + check_name):
        func = getattr(apply_path, check_name)
        try:
            func()
        except Exception as e:
            print(f'apply-path {check_name}: {e}')
        sys.exit(0)

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')

    check_name = subparsers.add_parser(check_name, help='Check path consistency')
    update_name = subparsers.add_parser(
        update_name,
        help='Update: set target path values to the values of source path; manual commit necessary',
    )

    args = vars(parser.parse_args())
    if args.get('subcommand') is None:
        parser.print_help()
        sys.exit()

    func = getattr(apply_path, args['subcommand'])
    del args['subcommand']

    res = ''
    try:
        res, rc = func(**args)
    except ApplyPathError as e:
        print(e)
        sys.exit(1)
    if res:
        print(res)
    sys.exit(rc)
