#!/usr/bin/env python3
#
# A utility to generate GraphQL schema defintions from standardized op-mode
# scripts.

import os
import sys
import json
import typing
import importlib.util
from inspect import signature, getmembers, isfunction
from jinja2 import Template

from vyos.opmode import _is_op_mode_function_name
from vyos.defaults import directories

# debugging code
local = True
if not local:
    OP_PATH = '/usr/libexec/vyos/op_mode/'
    SCHEMA_PATH = '/usr/libexec/vyos/services/api/graphql/graphql/schema/'
else:
    OP_PATH = '../../../../op_mode/'
    SCHEMA_PATH = './'
# end debugging code

# N.B. this will be moved to a separate file, similar to the use in configd
OP_FILES = ['cpu.py', 'memory.py', 'neighbor.py', 'route.py', 'version.py']

schema_data: dict = {'schema_name': '',
                     'schema_fields': []}

template  = """
input {{ schema_name }}Input {
    key: String!
    {%- for field_entry in schema_fields %}
    {{ field_entry }}
    {%- endfor %}
}

type {{ schema_name }} {
    result: String
}

type {{ schema_name }}Result {
    data: {{ schema_name }}
    success: Boolean!
    errors: [String]
}
"""

def _snake_to_pascal_case(name: str) -> str:
    res = ''.join(map(str.title, name.split('_')))
    return res

def _map_type_name(type_name: type, optional: bool = False) -> str:
    if type_name == str:
        return 'String!' if not optional else 'String'
    if type_name == int:
        return 'Int!' if not optional else 'Int'
    if type_name == bool:
        return 'Boolean!' if not optional else 'Boolean'
    if typing.get_origin(type_name) == list:
        if not optional:
            return f'[{_map_type_name(typing.get_args(type_name)[0])}]!'
        else:
            return f'[{_map_type_name(typing.get_args(type_name)[0])}]'
    # typing.Optional is typing.Union[_, NoneType]
    if (typing.get_origin(type_name) is typing.Union and
            typing.get_args(type_name)[1] == type(None)):
        return f'{_map_type_name(typing.get_args(type_name)[0], optional=True)}'

    # scalar 'Generic' is defined in schema.graphql
    return 'Generic'

# N.B. this construction should be moved to a utility script, as it is used
# elsewhere
def _load_as_module(name: str):
    path = os.path.join(OP_PATH, name)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def create_schema(func_name: str, base_name: str, func: callable) -> str:
    sig = signature(func)

    field_dict = {}
    for k in sig.parameters:
        field_dict[sig.parameters[k].name] = _map_type_name(sig.parameters[k].annotation)

    # It is assumed that if one is generating a schema for a 'show_*'
    # function, that 'get_raw_data' is present and 'raw' is desired.
    if 'raw' in list(field_dict):
        del field_dict['raw']

    schema_fields = []
    for k,v in field_dict.items():
        schema_fields.append(k+': '+v)

    schema_data['schema_name'] = _snake_to_pascal_case(func_name + '_' + base_name)
    schema_data['schema_fields'] = schema_fields

    j2_template = Template(template)
    res = j2_template.render(schema_data)

    return res

if __name__ == '__main__':
    from argparse import ArgumentParser

    for file in OP_FILES:
        module = _load_as_module(file)
        basename = os.path.splitext(file)[0]

        funcs = getmembers(module, isfunction)
        funcs = list(filter(lambda ft: _is_op_mode_function_name(ft[0]), funcs))

        funcs_dict = {}
        for (name, thunk) in funcs:
            funcs_dict[name] = thunk

        results = []
        for name,func in funcs_dict.items():
            res = create_schema(name, basename, func)
            results.append(res)

        out = '\n'.join(results)
        with open(f'./{basename}.graphql', 'w') as f:
            f.write(out)
