
from importlib import import_module
from typing import Any, Dict
from ariadne import ObjectType, convert_kwargs_to_snake_case, convert_camel_case_to_snake
from graphql import GraphQLResolveInfo
from makefun import with_signature

from vyos.template import render

from .. import state

mutation = ObjectType("Mutation")

def make_resolver(mutation_name):
    class_name = mutation_name.replace('create', '', 1)
    # and 'delete'
    func_base_name = convert_camel_case_to_snake(mutation_name).replace('create_', '', 1)
    func_name = f'resolve_create_{func_base_name}'
    func_sig = '(obj: Any, info: GraphQLResolveInfo, data: Dict)'

    @mutation.field(mutation_name)
    @convert_kwargs_to_snake_case
    @with_signature(func_sig, func_name=func_name)
    async def func_impl(*args, **kwargs):
        try:
            if 'data' not in kwargs:
                return {
                    "success": False,
                    "errors": ['missing data']
                }

            data = kwargs['data']
            session = state.settings['app'].state.vyos_session

            cmd_file = f'/usr/share/vyos/{func_base_name}.cmds'
            tmpl_file = f'graphql/{func_base_name}.tmpl'
            render(cmd_file, tmpl_file, data)

            mod = import_module(f'api.recipes.{func_base_name}')
            klass = getattr(mod, class_name)
            k = klass(session, cmd_file)
            k.configure()

            return {
                "success": True,
                "data": data
            }
        except Exception as error:
            return {
                "success": False,
                "errors": [str(error)]
            }

    return func_impl


