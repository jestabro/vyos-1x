#!/usr/bin/env python3
#
# Copyright (C) 2024 VyOS maintainers and contributors
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
#
#

import re
import json
import glob
from argparse import ArgumentParser
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element
from typing import TypedDict
from typing import TypeAlias
from typing import Optional
from typing import Union

from vyos.defaults import directories


class NodeData(TypedDict):
    node_type: Optional[str]
    help_text: Optional[str]
    command: Optional[str]
    path: Optional[list[str]]


OptElement: TypeAlias = Optional[Element]
PathData: TypeAlias = dict[str, Union[NodeData|list['PathData']]]
DEBUG = False


def translate_position(s: str, pos: list[str]) -> str:
    s = s.replace('${vyos_op_scripts_dir}', directories['op_mode'])
    s = s.replace('${vyos_libexec_dir}', directories['base'])
    pat: re.Pattern = re.compile(r'(?:\$([0-9]+))')
    t: str = pat.sub(r'{\1}', s)
    try:
        res: str = t.format(*pos)
    except IndexError as e:
        # op-mode definition file errors
        if DEBUG:
            print(f'{str(e)}: {s}; {pos}')
        res = t
    except KeyError:
        # does not extend to recursive definitions '{@:n}'
        res = t

    return res


def insert_node(n: Element, d: PathData, path = None) -> None:
    # pylint: disable=too-many-locals
    prop: OptElement = n.find('properties')
    children: OptElement = n.find('children')
    command: OptElement = n.find('command')
    # name is not None as required by schema
    name: str = n.get('name', 'schema_error')
    node_type: str = n.tag
    if path is None:
        path = []

    path.append(name)
    if node_type == 'tagNode':
        path.append(f'{name}-tag_value')

    help_prop: OptElement = None if prop is None else prop.find('help')
    help_text = None if help_prop is None else help_prop.text
    command_text = None if command is None else command.text
    if command_text is not None:
        pos = path.copy()
        pos.insert(0, '')
        command_text = translate_position(command_text, pos)

    # force list for type checking
    l: list = list(d.setdefault(name, []))
    inner_d: PathData = {'node_data': NodeData(node_type=node_type,
                                               help_text=help_text,
                                               command=command_text,
                                               path=path)}
    l.append(inner_d)

    if children is not None:
        inner_nodes = children.iterfind("*")
        for inner_n in inner_nodes:
            inner_path = path[:]
            insert_node(inner_n, inner_d, inner_path)


def parse_file(file_path, d):
    tree = ET.parse(file_path)
    root = tree.getroot()
    for n in root.iterfind("*"):
        insert_node(n, d)


def main():
    parser = ArgumentParser(description='generate dict from xml defintions')
    parser.add_argument('--xml-dir', type=str, required=True,
                        help='transcluded xml op-mode-definition file')
    parser.add_argument('--output-path', default='./op-mode-cache',
                        help='path to generated cache')
    args = parser.parse_args()
    xml_dir = args.xml_dir
    output_path = args.output_path

    d = {}
    l = [d]

    for fname in glob.glob(f'{xml_dir}/*.xml'):
        parse_file(fname, d)

    with open(output_path, 'w') as f:
        json.dump(l, f, indent=2)


if __name__ == '__main__':
    main()
