#!/usr/bin/env python3
#
# Copyright (C) 2023 VyOS maintainers and contributors
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

import sys
import json
import argparse
from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import isdir

_here = dirname(__file__)

sys.path.append(join(_here, '..'))
from configtree import reference_tree_to_json, ConfigTreeError

xml_cache = abspath(join(_here, 'cache.py'))
xml_tmp = '/tmp/xml_cache.json'

node_data_fields = ("node_type", "multi", "valueless", "default_value")

def trim_cache(some_dict: dict):
    for k in list(some_dict):
        if k == "node_data":
            for l in list(some_dict[k]):
                if l not in node_data_fields:
                    del some_dict[k][l]
        else:
            if isinstance(some_dict[k], dict):
                trim_cache(some_dict[k])

def main():
    parser = argparse.ArgumentParser(description='generate and save dict from xml defintions')
    parser.add_argument('--xml-dir', type=str, required=True,
                        help='transcluded xml interface-definition directory')
    args = parser.parse_args()

    xml_dir = abspath(args.xml_dir)

    try:
        reference_tree_to_json(xml_dir, xml_tmp)
    except ConfigTreeError as e:
        print(e)
        sys.exit(1)

    with open(xml_tmp) as f:
        d = json.loads(f.read())

    trim_cache(d)

    with open(xml_cache, 'w') as f:
        f.write(f'reference = {str(d)}')

if __name__ == '__main__':
    main()
