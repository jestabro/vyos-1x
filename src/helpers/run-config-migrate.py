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
                    help="configuration file to modify with system-specific settings")
parser.add_argument('--test-script', type=str,
                    help="test effect of named script")

args = parser.parse_args()

checkpoint_file = '/run/vyos-migrate-checkpoint'

if 'vyos-migrate-debug' in Path('/proc/cmdline').read_text():
    print(f'\nmigrate-debug enabled: file {checkpoint_file}_* on error')
    debug = checkpoint_file
else:
    debug = None

config_migrate = ConfigMigrate(args.config_file)

if args.test_script:
    # run_script
    sys.exit(0)

begin = datetime.now()
config_migrate.run()
end = datetime.now()
print(f'JSE load time: {end - begin}')
