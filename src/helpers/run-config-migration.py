#!/usr/bin/python3

import os
import sys
import argparse
import datetime
import subprocess
from vyos.migrator import Migrator

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('config_file', type=str,
            help="configuration file to migrate")
    args = argparser.parse_args()

    config_file_name = args.config_file

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

#    migration = VirtualMigrator(config_file_name)
    migration = Migrator(config_file_name)

    migration.run()

if __name__ == '__main__':
    main()
