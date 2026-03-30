#!/usr/bin/env python3
#
# Copyright VyOS maintainers and contributors <maintainers@vyos.io>
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
from pathlib import Path


parser = ArgumentParser()
parser.add_argument(
    'new_list',
    type=str,
    help='new activation list',
)

parser.add_argument(
    'orig_list',
    type=str,
    help='original activation list',
)

args = parser.parse_args()
orig_list = args.orig_list
new_list = args.new_list


def read_list(path: str):
    file = Path(path).read_text()
    return json.loads(file)


def write_list(obj: dict, path: str):
    Path(path).write_text(json.dumps(obj))


def stable_update(new: dict, old: dict):
    res = {}
    for key in new.keys():
        res[key] = old[key] if key in old.keys() else new[key]
    return res


if not Path(new_list).exists():
    sys.exit('Missing activation list!')

if Path(orig_list).exists():
    ob = stable_update(read_list(new_list), read_list(orig_list))
else:
    ob = read_list(new_list)

write_list(ob, orig_list)
