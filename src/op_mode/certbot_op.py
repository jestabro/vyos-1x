#!/usr/bin/env python3

import sys
import argparse

import vyos.defaults
from vyos.util import cmd, call
from vyos.configquery import query_context
from vyos.certbot_util import CertbotData

vyos_certbot_dir = vyos.defaults.directories['certbot']

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
    c = CertbotData()
    cert_name = args.cert_name
    cert_name = c.certificate_name_from_domain(cert_name)

    revoke_cmd = f'sudo certbot revoke --test-cert --delete-after-revoke --noninteractive --config-dir {vyos_certbot_dir} --cert-name {cert_name}'
    revoke_out = cmd(revoke_cmd, raising=RuntimeError, message="certbot revoke failed")
    print(f"revoke_cmd is {revoke_cmd}")
    print(f"revoke: {revoke_out}")

def show_cert_names():
    c = CertbotData()
    for n in c.names:
        print(n)

def show_domains():
    c = CertbotData()
    for n in c.names:
        print(c.names[n]['domains'])

def show_paths():
    c = CertbotData()
    for n in c.names:
        print(c.names[n]['path'])

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
