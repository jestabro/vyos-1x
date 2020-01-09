#!/usr/bin/env python3
#
# Copyright (C) 2019 VyOS maintainers and contributors
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
#
#

import os
import sys
import json
import logging

import vyos.component

debug = True

logger = logging.getLogger('vyos.component')
log_handler = logging.StreamHandler()
logger.addHandler(log_handler)

if debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

def main():
    try:
        vyos.component.update_system_versions()
    except Exception as err:
        sys.exit(err)

if __name__ == "__main__":
    main()
