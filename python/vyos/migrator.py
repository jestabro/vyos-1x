import sys
import os
import re
import subprocess
import vyos.version
import vyos.migration_defaults
import vyos.systemversions as systemversions
import vyos.formatversions as formatversions

class MigratorError(Exception):
    pass

class Migrator(object):
    def __init__(self, config_file, forced=False, set_vintage=None):
        self._config_file = config_file
        self._forced = forced
        self._set_vintage = set_vintage
        self._config_file_vintage = None
        pass

    def get_config_file_versions(self):
        """
        Get component versions from config file; return empty dictionary if
        config string is missing.
        """
        cfg_file = self._config_file
        component_versions = {}

        cfg_versions = formatversions.read_vyatta_versions(cfg_file)

        if bool(cfg_versions):
            self._config_file_vintage = 'vyatta'
            component_versions = cfg_versions

        cfg_versions = formatversions.read_vyos_versions(cfg_file)

        if bool(cfg_versions):
            self._config_file_vintage = 'vyos'
            component_versions = cfg_versions

        return component_versions

    def run_migration_scripts(self, config_file_versions, system_versions):
        cfg_versions = config_file_versions
        sys_versions = system_versions

        for key in cfg_versions.keys() - sys_versions.keys():
            sys_versions[key] = 0

        sys_keys = list(sys_versions.keys())
        sys_keys.sort()

        rev_versions = {}

        for key in sys_keys:
            sys_ver = sys_versions[key]
            if key in cfg_versions:
                cfg_ver = cfg_versions[key]
            else:
                cfg_ver = 0

            migrate_script_dir = os.path.join(
                    vyos.migration_defaults.vyatta_migrate_script_dir, key)

            while cfg_ver != sys_ver:
                if cfg_ver < sys_ver:
                    next_ver = cfg_ver + 1
                else:
                    next_ver = cfg_ver - 1

                migrate_script = os.path.join(migrate_script_dir,
                        '{}-to-{}'.format(cfg_ver, next_ver))

                try:
                    subprocess.check_output([migrate_script,
                        self._config_file])
                except FileNotFoundError:
                    pass
                except subprocess.CalledProcessError as err:
                    print("Called process error: {}.".format(err))
                    sys.exit(1)

                cfg_ver = next_ver

            rev_versions[key] = cfg_ver

        return rev_versions

    def write_config_file_versions(self, config_versions):
        """
        Write new version string.
        """
        component_version_string = formatversions.format_versions_string(config_versions)

        os_version_string = vyos.version.get_version()

        if self._set_vintage:
            self._config_file_vintage = self._set_vintage

        if not self._config_file_vintage:
            self._config_file_vintage = vyos.migration_defaults.default_vintage

        if self._config_file_vintage == 'vyatta':
            formatversions.write_vyatta_versions_foot(self._config_file,
                                         component_version_string,
                                         os_version_string)

        if self._config_file_vintage == 'vyos':
            formatversions.write_vyos_versions_foot(self._config_file,
                                        component_version_string,
                                        os_version_string)

    def run(self):
        cfg_file = self._config_file

        if not self._forced:
            cfg_versions = self.get_config_file_versions()
        else:
            # This will force calling all migration scripts.
            cfg_versions = {}

        sys_versions = systemversions.get_system_versions()

        rev_versions = self.run_migration_scripts(cfg_versions, sys_versions)

        formatversions.remove_versions(cfg_file)

        self.write_config_file_versions(rev_versions)


class VirtualMigrator(Migrator):
    def __init__(self, config_file, vintage='vyos'):
        super().__init__(config_file, set_vintage = vintage)

    def run(self):
        cfg_file = self._config_file

        cfg_versions = self.get_config_file_versions()
        if not bool(cfg_versions):
            print("Config file has no version information; virtual "
                  "migration not possible")
            sys.exit(0)

        formatversions.remove_versions(cfg_file)

        self.write_config_file_versions_string(cfg_versions)

