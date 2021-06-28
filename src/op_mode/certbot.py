#!/usr/bin/env python3

import os
import re
import sys
import argparse

import vyos.defaults
from vyos.util import cmd, call
from vyos.configquery import query_context

vyos_certbot_dir = vyos.defaults.directories['certbot']

def get_certbot_info():
    '''Gather the output of 'certbot certificate' into a dictionary; certbot
    could really use an API.
    '''
    show_cmd = f'sudo certbot --config-dir {vyos_certbot_dir} certificates'
    show_out = cmd(show_cmd, raising=RuntimeError,
                   message="certbot certificates failed")
    info = re.split(r'.(?=Certificate Name)', show_out)
    info = [l for l in info if 'Certificate Name' in l]
    certbot_info = {}
    for entry in info:
        lines = entry.splitlines()
        for line in lines:
            if 'Certificate Name' in line:
                name = line.split()[2]
                certbot_info[name] = {}
            if 'Domains' in line:
                certbot_info[name]['domains'] = line.split()[1:]
            if 'Certificate Path' in line:
                path = line.split()[2:][0]
                path = os.path.split(path)[0]
                certbot_info[name]['path'] = path
    return certbot_info

def _certificate_name_from_domain(domain: str):
    info = get_certbot_info()
    for n in list(info):
        if domain in info[n]['domains']:
            return n
    return None

def request():
    query, _ = query_context()

    if (not query.exists(['system', 'name-server']) and
        not query.exists(['system', 'name-servers-dhcp'])):
        print("certbot will need a name-server in order to resolve the domains in question; please set 'name-server' or 'name-servers-dhcp'")
        sys.exit(1)

    email = args.email
    domains = args.domains

    if email != 'none':
        email_flag = '-m {0}'.format(email)
    else:
        email_flag = '--register-unsafely-without-email'

    if domains is not None:
        domain_flag = '-d ' + ' -d '.join(domains)
    else:
        domain_flag = ''

    certbot_cmd = f'certbot certonly --test-cert --config-dir {vyos_certbot_dir} -n --nginx --agree-tos --no-eff-email --expand {email_flag} {domain_flag}'

    print(f"certbot_cmd is {certbot_cmd}")

    cmd(certbot_cmd,
        raising=RuntimeError,
        message="The certbot request failed for the specified domains.")

    call('systemctl restart certbot.timer')

def revoke():
    cert_name = args.cert_name
    cert_name = _certificate_name_from_domain(cert_name)

    revoke_cmd = f'sudo certbot revoke --test-cert --delete-after-revoke --noninteractive --config-dir {vyos_certbot_dir} --cert-name {cert_name}'
    revoke_out = cmd(revoke_cmd, raising=RuntimeError, message="certbot revoke failed")
    print(f"revoke_cmd is {revoke_cmd}")
    print(f"revoke: {revoke_out}")

def show_cert_names():
    info = get_certbot_info()
    for n in list(info):
        print(n)

def show_domains():
    info = get_certbot_info()
    for n in list(info):
        print(info[n]['domains'])

def show_paths():
    info = get_certbot_info()
    for n in list(info):
        print(info[n]['path'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Request Let's Encrypt certificate")
    parser.add_argument('--request', action='store_true')
    parser.add_argument('--revoke', action='store_true')
    parser.add_argument('--show-domains', action='store_true')
    parser.add_argument('--show-paths', action='store_true')
    parser.add_argument('--show-certs', action='store_true')
    parser.add_argument('--email', action='store', type=str)
    parser.add_argument('--domains', nargs='+')
    parser.add_argument('--cert-name', action='store', type=str)

    args = parser.parse_args()

    print(f"email is {args.email}")
    print(f"domains are {args.domains}")

    try:
        if args.request:
            request()
        if args.revoke:
            revoke()
        if args.show_certs:
            show_cert_names()
        if args.show_domains:
            show_domains()
        if args.show_paths:
            show_paths()
    except RuntimeError as e:
        print(e)
        sys.exit(1)
