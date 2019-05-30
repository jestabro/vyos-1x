#!/usr/bin/python3

import os
import sys
import argparse
import datetime
import subprocess
from vyos.migrator import Migrator, VirtualMigrator

def main():
    argparser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument('config_file', type=str,
            help="configuration file to migrate")
    argparser.add_argument('--force', action='store_true',
            help="Force calling of all migration scripts.")
    argparser.add_argument('--set-vintage', type=str,
            help="Set the format for the config version footer in config"
            " file:\n"
            "set to 'vyatta':\n"
            "(for '/* === vyatta-config-version ... */' format)\n"
            "or 'vyos':\n"
            "(for '// vyos-config-version ...' format).")
    argparser.add_argument('--virtual', action='store_true',
            help="Update the format of the trailing comments in"
                 " config file,\nfrom 'vyatta' to 'vyos'; no migration"
                 " scripts are run.")
    args = argparser.parse_args()

    config_file_name = args.config_file
    force_on = args.force
    vintage = args.set_vintage
    virtual = args.virtual

    if not os.access(config_file_name, os.R_OK):
        print("Read error: {}.".format(config_file_name))
        sys.exit(1)

    if not os.access(config_file_name, os.W_OK):
        print("Write error: {}.".format(config_file_name))
        sys.exit(1)

    separator = "."
    backup_file_name = separator.join([config_file_name,
            '{0:%Y-%m-%d-%H%M}'.format(datetime.datetime.now()),
            'pre-migration'])

    try:
        subprocess.check_call(['cp', '-p', config_file_name,
                backup_file_name])
    except subprocess.CalledProcessError as err:
        print("Called process error: {}.".format(err))
        sys.exit(1)

    if not virtual:
        migration = Migrator(config_file_name, force=force_on,
                             set_vintage=vintage)
    else:
        migration = VirtualMigrator(config_file_name)

    migration.run()

if __name__ == '__main__':
    main()
