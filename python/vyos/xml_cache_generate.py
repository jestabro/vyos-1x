#!/usr/bin/env python3

import json
import argparse
from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import isdir

from configtree import reference_tree_to_json

_here = dirname(__file__)

xml_cache = abspath(join(_here, 'xml_cache.py'))
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

    reference_tree_to_json(xml_dir, xml_tmp)

    with open(xml_tmp) as f:
        d = json.loads(f.read())

    trim_cache(d)

    with open(xml_cache, 'w') as f:
        f.write(f'definition = {str(d)}')

if __name__ == '__main__':
    main()
