#!/usr/bin/env python3
#
# Copyright (C) 2019-2020 VyOS maintainers and contributors
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
import os

import vyos.defaults
from vyos.config import Config
from vyos import ConfigError
from vyos.util import cmd
from vyos.util import call

from vyos import airbag
airbag.enable()

vyos_conf_scripts_dir = vyos.defaults.directories['conf_mode']
vyos_certbot_dir = vyos.defaults.directories['certbot']

dependencies = [
    'https.py',
]

def get_certbot_domains():
    show_cmd = f'sudo certbot --config-dir {vyos_certbot_dir} certificates'
    show_out = cmd(show_cmd, raising=RuntimeError, message="certbot show failed")
    lines = show_out.splitlines()
    domains = []
    for line in lines:
        if 'Domains' in line:
            domains = domains + line.split()[1:]
    return domains

def request_certbot(cert):
    email = cert.get('email')
    if email is not None:
        email_flag = '-m {0}'.format(email)
    else:
        email_flag = ''

    domains = cert.get('domains')
    if domains is not None:
        domain_flag = '-d ' + ' -d '.join(domains)
    else:
        domain_flag = ''

    certbot_cmd = f'certbot certonly --config-dir {vyos_certbot_dir} -n --nginx --agree-tos --no-eff-email --expand {email_flag} {domain_flag}'

    cmd(certbot_cmd,
        raising=ConfigError,
        message="The certbot request failed for the specified domains.")

def get_config():
    conf = Config()
    if not conf.exists('service https certificates certbot'):
        return None
    else:
        conf.set_level('service https certificates certbot')

    cert = {}

    if conf.exists('domain-name'):
        cert['domains'] = conf.return_values('domain-name')

    if conf.exists('email'):
        cert['email'] = conf.return_value('email')

    return cert

def verify(cert):
    if cert is None:
        return None

    if 'domains' not in cert:
        raise ConfigError("At least one domain name is required to"
                          " request a letsencrypt certificate.")

# check against existing domains
    domains = get_certbot_domains()
    domain = cert['domains']
    if domain not in domains:
        raise ConfigError(f'No existing certificate for domain {domain}; please execute:\n "run generate certbot email <email addr> domains {domain}"')
# remove all email refs

    if 'email' not in cert:
        raise ConfigError("An email address is required to request"
                          " a letsencrypt certificate.")

def generate(cert):
    if cert is None:
        return None

    # certbot will attempt to reload nginx, even with 'certonly';
    # start nginx if not active
#    ret = call('systemctl is-active --quiet nginx.service')
#    if ret:
#        call('systemctl start nginx.service')

# remove this
#    request_certbot(cert)

def apply(cert):
    if cert is not None:
        call('systemctl restart certbot.timer')
    else:
        call('systemctl stop certbot.timer')
        return None

    for dep in dependencies:
        cmd(f'{vyos_conf_scripts_dir}/{dep}', raising=ConfigError)

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        sys.exit(1)

