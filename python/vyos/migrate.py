# Copyright 2019-2024 VyOS maintainers and contributors <maintainers@vyos.io>
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

import os
import re
import json
import logging
from pathlib import Path
from grp import getgrnam
import datetime

from vyos.utils.process import cmd

import vyos.defaults
from vyos.configtree import ConfigTree
from vyos.component_version import VersionInfo
from vyos.component_version import version_info_from_system
from vyos.component_version import version_info_from_file
from vyos.component_version import version_info_copy
from vyos.component_version import version_info_prune_component
from vyos.compose_config import ComposeConfig
from vyos.compose_config import ComposeConfigError


log_file = os.path.join(vyos.defaults.directories['config'], 'vyos-migrate.log')

def group_perm_file_handler(filename, group=None, mode='a'):
    # pylint: disable=consider-using-with
    if group is None:
        return logging.FileHandler(filename, mode)
    gid = getgrnam(group).gr_gid
    if not os.path.exists(filename):
        open(filename, 'a').close()
        os.chown(filename, -1, gid)
        os.chmod(filename, 0o664)
    return logging.FileHandler(filename, mode)

class ConfigMigrate:
    # pylint: disable=too-many-instance-attributes,too-many-arguments
    # the number is reasonable in this case
    def __init__(self, config_file: str, force=False, stream_log=False,
                 output_file: str = None, checkpoint_file: str = None):
        self.config_file: str = config_file
        self.force: bool = force
        self.system_version: VersionInfo = version_info_from_system()
        self.file_version: VersionInfo = version_info_from_file(self.config_file)
        self.compose = None
        self.output_file = output_file
        self.checkpoint_file = checkpoint_file
        self.logger = None
        self.stream_log: bool = stream_log

        if self.file_version is None:
            raise ValueError(f'failed to read config file {self.config_file}')

    def init_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

#        fh = logging.FileHandler(log_file, mode='w')
        fh = group_perm_file_handler(log_file, group='vyattacfg', mode='w')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        if self.stream_log:
            ch = logging.StreamHandler()
            ch.setLevel(logging.WARNING)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def migration_needed(self) -> bool:
        return self.system_version.component != self.file_version.component

    def release_update_needed(self) -> bool:
        return self.system_version.release != self.file_version.release

    def syntax_update_needed(self) -> bool:
        return self.system_version.vintage != self.file_version.vintage

    def update_release(self):
        """
        Update config file release version.
        """
        self.file_version.update_release(self.system_version.release)

    def update_syntax(self):
        """
        Update config file syntax.
        """
        self.file_version.update_syntax()

    def normalize_config_body(self, version_info: VersionInfo):
        """
        This is a interim workaround for the issue of node ordering when
        composing operations on the internal config_tree: ordering is
        performed on parsing, hence was implicit in the old system which
        would parse/write on each application of a migration script (~200).
        Here, we will take the cost of one extra parsing to reorder before
        save.
        """
        if not version_info.config_body_is_none():
            ct = ConfigTree(version_info.config_body)
            version_info.update_config_body(ct.to_string())

    def write_config(self):
        if self.output_file is not None:
            config_file = self.output_file
        else:
            config_file = self.config_file

        self.file_version.write(config_file)

    @staticmethod
    def sort_function():
        numbers = re.compile(r'(\d+)')
        def func(p: Path):
            parts = numbers.split(p.stem)
            return list(map(int, parts[1::2]))
        return func

    @staticmethod
    def file_ext(file_path: Path) -> str:
        """Return an identifier from file name for checkpoint file extension.
        """
        return f'{file_path.parent.stem}_{file_path.stem}'

    def run_migration_scripts(self):
        """
        Run migration scripts iteratively, until config file version equals
        system component version.
        """
        os.environ['VYOS_MIGRATION'] = '1'
        self.init_logger()
        self.logger.info("List of applied migration modules:")

        components = list(self.system_version.component)
        components.sort()

        # T4382: 'bgp' needs to follow 'quagga':
        if 'bgp' in components and 'quagga' in components:
            components.insert(components.index('quagga'),
                              components.pop(components.index('bgp')))

        revision: VersionInfo = version_info_copy(self.file_version)
        version_info_prune_component(revision, self.system_version)

        migrate_dir = Path(vyos.defaults.directories['migrate'])
        sort_func = ConfigMigrate.sort_function()

        for key in components:
            p = migrate_dir.joinpath(key)
            script_list = list(p.glob('*-to-*'))
            script_list = sorted(script_list, key=sort_func)

            if not self.file_version.component_is_none() and not self.force:
                start = self.file_version.component.get(key, 0)
                script_list = list(filter(lambda x, st=start: sort_func(x)[0] >= st,
                                          script_list))

            if not script_list: # no applicable migration scripts
                revision.update_component(key, self.system_version.component[key])
                continue

            for file in script_list:
                f = file.as_posix()
                self.logger.info(f'applying {f}')
                try:
                    self.compose.apply_file(f, func_name='migrate')
                except ComposeConfigError as e:
                    self.logger.error(e)
                    if self.checkpoint_file:
                        check = f'{self.checkpoint_file}_{ConfigMigrate.file_ext(file)}'
                        revision.update_config_body(self.compose.to_string())
                        revision.write(check)
                    break
                else:
                    revision.update_component(key, sort_func(file)[1])
#                    revision.update_config_body(self.compose.to_string())

        revision.update_config_body(self.compose.to_string())
        self.normalize_config_body(revision)
        self.file_version = version_info_copy(revision)
        # backup file
        # write partial/full in place
        # warn/error if partial

        if revision.component == self.system_version.component:
            pass

        del os.environ['VYOS_MIGRATION']

    def save_json_record(self):
        """
        Write component versions to a json file
        """
#        mask = os.umask(0o113)
        version_file = vyos.defaults.component_version_json

        try:
            with open(version_file, 'w') as f:
                f.write(json.dumps(self.system_version.component,
                                   indent=2, sort_keys=True))
        except OSError:
            pass
#        finally:
#            os.umask(mask)

    def load_config(self):
        """
        Instantiate a ComposeConfig object with the config string.
        """

        self.compose = ComposeConfig(self.file_version.config_body, self.checkpoint_file)

    def backup(self):
        # pylint: disable=consider-using-f-string
        separator = "."
        backup = separator.join([self.config_file,
                                 '{0:%Y-%m-%d-%H%M%S}'.format(datetime.datetime.now()),
                                 'pre-migration'])
        cmd(f'cp -p {self.config_file} {backup}')

    def run(self):
        """
        If migration needed, run migration scripts and update config file.
        If only release version update needed, update release version.
        """
        # save system component versions in json file for reference
        self.save_json_record()

        if not self.migration_needed():
            if self.release_update_needed():
                self.update_release()
                self.write_config()
            return

        if self.syntax_update_needed():
            self.update_syntax()
            self.write_config()

        self.backup()

        self.load_config()

        self.run_migration_scripts()

        self.update_release()
        self.write_config()

    def run_script(self, test_script: str):
        """
        Run a single migration script. For testing this simply provides the
        body for loading and writing the result; the component string is not
        updated.
        """

        self.load_config()
        self.init_logger()

        os.environ['VYOS_MIGRATION'] = '1'

        try:
            self.compose.apply_file(test_script, func_name='migrate')
        except ComposeConfigError as e:
            print(f'config-migration error in {test_script}: {e}')
        else:
            self.file_version.update_config_body(self.compose.to_string())

        del os.environ['VYOS_MIGRATION']

        self.write_config()
