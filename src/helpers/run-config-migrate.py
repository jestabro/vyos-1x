#!/usr/bin/env python3
#
# Copyright (C) 2024 VyOS maintainers and contributors
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
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

from vyos.migrate import ConfigMigrate

parser = ArgumentParser()
parser.add_argument('config_file', type=str,
                    help="configuration file to migrate")
parser.add_argument('--test-script', type=str,
                    help="test named script")
parser.add_argument('--output-file', type=str,
                    help="write to named output file instead of config file")
parser.add_argument('--debug', action='store_true',
                    help="write checkpoint file on error")
parser.add_argument('--force', action='store_true',
                    help="force run of all migration scripts")


args = parser.parse_args()

checkpoint_file = '/tmp/vyos-migrate-checkpoint'

debug = args.debug

if debug:
    debug = checkpoint_file

if 'vyos-migrate-debug' in Path('/proc/cmdline').read_text():
    print(f'\nmigrate-debug enabled: file {checkpoint_file}_* on error')
    debug = checkpoint_file

config_migrate = ConfigMigrate(args.config_file, force=args.force,
                               checkpoint_file=debug, output_file=args.output_file)

if args.test_script:
    # run_script and exit
#    config_migrate.run_script(args.test_script)
    sys.exit(0)

begin = datetime.now()
config_migrate.run()
end = datetime.now()
print(f'JSE load time: {end - begin}')
