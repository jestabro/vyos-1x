#!/usr/bin/env python3
#
# Copyright (C) 2023-2025 VyOS maintainers and contributors
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
import json
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from os.path import join
from os.path import abspath
from os.path import dirname
from xmltodict import parse


_here = dirname(__file__)

sys.path.append(join(_here, '..'))
from configtree import ConfigTreeError
from configtree import interface_definition_to_cache
from configtree import reference_tree_cache_to_json

# fields to retain in the dict representation of the XML reference tree
node_data_fields = ("node_type", "multi", "valueless", "default_value",
                    "owner", "priority")

class Arg:
    dict_cache = abspath(join(_here, 'cache.py'))
    component_cache = abspath(join(_here, 'component_cache.py'))

def non_trivial(s: str) -> str:
    if not s:
        raise ArgumentTypeError("Argument must be non empty string")
    if ' ' in s:
        raise ArgumentTypeError("Argument must not contain spaces")
    return s


def parse_arguments() -> Arg:
    parser : ArgumentParser = ArgumentParser(
        description='generate reference tree from xml definitions and'
                    'save Python dict representation'
        )

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--generate', action='store_true',
                        help='Generate package cache from xml definitions')
    action.add_argument('--install', action='store_true',
                        help='Install reference cache from package cache(s)')

    parser.add_argument('--xml-dir', type=str, required=True,
                        help='transcluded xml interface-definition directory')
    parser.add_argument('--cache-dir', type=str, required=True,
                        help='location for unrendered json data for loading by vyconfd')
    parser.add_argument('--pkg-name', type=non_trivial, required=True,
                        help='package name for the cache')

    return parser.parse_args(namespace=Arg())


def store_component_version(arg: Arg) -> None:
    syntax_version = join(xml_dir, 'xml-component-version.xml')
    try:
        with open(syntax_version) as f:
            component = f.read()
    except FileNotFoundError:
        if pkg_name != 'vyos_1x':
            component = ''
        else:
            print("\nWARNING: missing xml-component-version.xml\n")
            sys.exit(1)

    if component:
        parsed = parse(component)
    else:
        parsed = None
    version = {}
    # addon package definitions may have empty (== 0) version info
    if parsed is not None and parsed['interfaceDefinition'] is not None:
        converted = parsed['interfaceDefinition']['syntaxVersion']
        if not isinstance(converted, list):
            converted = [converted]
        for i in converted:
            tmp = {i['@component']: i['@version']}
            version |= tmp

    version = {"component_version": version}

    try:
        with open(arg.component_cache, 'r') as f:
            component = f.read()
    except FileNotFoundError:
        component = {}


    component |= version

    with open(arg.component_cache, 'w') as f:
        f.write(json.dumps(component))


def generate_cache(arg: Arg) -> None:
    dest = abspath(join(cache_dir, pkg_name))
    try:
        interface_definition_to_cache(xml_dir, dest)
    except ConfigTreeError as e:
        sys.exit(e)

    if pkg_name == 'vyos-1x':
        reference_tree_cache_to_json(dest, Arg.dict_cache)

def install_cache(cache_dir: str, pkg_name: str) -> None:

def main():
    arg = parse_arguments()
    print(arg.dict_cache)

    dest = abspath(join(arg.cache_dir, arg.pkg_name))
    try:
        interface_definition_to_cache(arg.xml_dir, dest)
    except ConfigTreeError as e:
        sys.exit(e)

    if arg.pkg_name == 'vyos-1x':
        reference_tree_cache_to_json(dest, arg.dict_cache)

if __name__ == '__main__':
    main()
