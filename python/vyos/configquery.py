# Copyright 2021 VyOS maintainers and contributors <maintainers@vyos.io>
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
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

'''
A small library that allows querying existence or value(s) of config
settings from op mode, and execution of arbitrary op mode commands.
'''

import os
from subprocess import STDOUT
from vyos.util import popen, dict_search
from vyos.configsession import ConfigSession, ConfigSessionError
from vyos.config import Config


class ConfigQueryError(Exception):
    pass

class GenericConfigQuery:
    def __init__(self):
        pass

    def exists(self, path: list):
        raise NotImplementedError

    def value(self, path: list):
        raise NotImplementedError

    def values(self, path: list):
        raise NotImplementedError

class GenericOpRun:
    def __init__(self):
        pass

    def run(self, path: list, **kwargs):
        raise NotImplementedError

class CliShellApiConfigQuery(GenericConfigQuery):
    def __init__(self):
        super().__init__()

    def exists(self, path: list):
        cmd = ' '.join(path)
        (_, err) = popen(f'cli-shell-api existsActive {cmd}')
        if err:
            return False
        return True

    def value(self, path: list):
        cmd = ' '.join(path)
        (out, err) = popen(f'cli-shell-api returnActiveValue {cmd}')
        if err:
            raise ConfigQueryError('No value for given path')
        return out

    def values(self, path: list):
        cmd = ' '.join(path)
        (out, err) = popen(f'cli-shell-api returnActiveValues {cmd}')
        if err:
            raise ConfigQueryError('No values for given path')
        return out

class ConfigDictQuery(GenericConfigQuery):
    def __init__(self):
        super().__init__()
        self.session = ConfigSession(os.getpid())
        env = self.session.get_session_env()
        self.config = Config(session_env=env)

    def get_config_dict(self, path=[], effective=False, key_mangling=None,
                        get_first_key=False, no_multi_convert=False,
                        no_tag_node_value_mangle=False):

        config_dict = self.config.get_config_dict(path=path, effective=effective,
                                                  key_mangling=key_mangling,
                                                  get_first_key=get_first_key,
                                                  no_multi_convert=no_multi_convert,
                                                  no_tag_node_value_mangle=no_tag_node_value_mangle)

        return config_dict

    def exists(self, path: list):
        config_dict = self.get_config_dict()
        dpath = '.'.join(path)
        res = dict_search(dpath, config_dict)
        if res:
            return True
        return False

    # currently there is no distinction between the following two functions,
    # nor can there be, pending the resolution of T3234.
    def value(self, path: list):
        config_dict = self.get_config_dict()
        dpath = '.'.join(path)
        res = dict_search(dpath, config_dict)
        return res

    def values(self, path: list):
        config_dict = self.get_config_dict()
        dpath = '.'.join(path)
        res = dict_search(dpath, config_dict)
        return res

class VbashOpRun(GenericOpRun):
    def __init__(self):
        super().__init__()

    def run(self, path: list, **kwargs):
        cmd = ' '.join(path)
        (out, err) = popen(f'.  /opt/vyatta/share/vyatta-op/functions/interpreter/vyatta-op-run; _vyatta_op_run {cmd}', stderr=STDOUT, **kwargs)
        if err:
            raise ConfigQueryError(out)
        return out

def query_context(config_query_class=CliShellApiConfigQuery,
                  op_run_class=VbashOpRun):
    query = config_query_class()
    run = op_run_class()
    return query, run


