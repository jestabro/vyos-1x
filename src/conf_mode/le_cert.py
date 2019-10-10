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

import sys
import os
import subprocess

import vyos.defaults
from vyos.config import Config
from vyos import ConfigError

vyos_conf_scripts_dir = vyos.defaults.directories['conf_mode']

# XXX: this model will need to be extended for tag nodes
dependencies = [
    'https.py',
]

def get_config():
    le_cert = vyos.defaults.le_cert_data

    conf = Config()
    if not conf.exists('service https certificates letsencrypt-certificate'):
        return None
    else:
        conf.set_level('service https certificates letsencrypt-certificate')

    if conf.exists('domain-name'):
        le_cert['domains'] = conf.return_values('lifetime')

    if conf.exists('email'):
        le_cert['email'] = conf.return_value('email')

    return le_cert

def verify(le_cert):
    if not le_cert['domains']:
        raise ConfigError("at least one domain name is required to"
                          " request a letsencrypt certificate")

def generate(le_cert):
    if le_cert is None:
        return None

    request_if_needed_letsencrypt(le_cert)

def apply(le_cert):
    for dep in dependencies:
        cmd = '{0}/{1}'.format(vyos_conf_scripts_dir, dep)
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as err:
            raise ConfigError("{}.".format(err))

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        sys.exit(1)

