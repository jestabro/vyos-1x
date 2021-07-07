# certbot_util -- various helper functions
# includes an adaptation of certbot_nginx name matching functions for VyOS
# https://github.com/certbot/certbot/blob/master/LICENSE.txt

import os
import re

import vyos.defaults
from vyos.util import cmd
from certbot_nginx._internal import parser

vyos_certbot_dir = vyos.defaults.directories['certbot']

class CertbotData:
    def __init__(self):
        '''Gather the output of 'certbot certificate' into a dictionary; certbot
        could really use a library API (cf.
        https://github.com/certbot/certbot/issues/4065).
        '''
        self.names = {}
        show_cmd = f'sudo certbot --config-dir {vyos_certbot_dir} certificates'
        show_out = cmd(show_cmd, raising=RuntimeError,
                       message="certbot certificates failed")
        info = re.split(r'.(?=Certificate Name)', show_out)
        info = [l for l in info if 'Certificate Name' in l]
        for entry in info:
            lines = entry.splitlines()
            for line in lines:
                if 'Certificate Name' in line:
                    name = line.split()[2]
                    self.names[name] = {}
                if 'Domains' in line:
                    self.names[name]['domains'] = line.split()[1:]
                if 'Certificate Path' in line:
                    path = line.split()[2:][0]
                    path = os.path.split(path)[0]
                    self.names[name]['path'] = path

    def certificate_name_from_domain(self, domain: str):
        '''Get the 'certificate name' from a given domain name (this is also
        a path component for cert location).
        '''
        for n in self.names:
            if domain in self.names[n]['domains']:
                return n
        return None


NAME_RANK = 0
START_WILDCARD_RANK = 1
END_WILDCARD_RANK = 2
REGEX_RANK = 3

def _rank_matches_by_name(server_block_list, target_name):
    """Returns a ranked list of server_blocks that match target_name.
    Adapted from the function of the same name in
    certbot_nginx.NginxConfigurator
    """
    matches = []
    for server_block in server_block_list:
        name_type, name = parser.get_best_match(target_name,
                                                server_block['name'])
        if name_type == 'exact':
            matches.append({'vhost': server_block,
                            'name': name,
                            'rank': NAME_RANK})
        elif name_type == 'wildcard_start':
            matches.append({'vhost': server_block,
                            'name': name,
                            'rank': START_WILDCARD_RANK})
        elif name_type == 'wildcard_end':
            matches.append({'vhost': server_block,
                            'name': name,
                            'rank': END_WILDCARD_RANK})
        elif name_type == 'regex':
            matches.append({'vhost': server_block,
                            'name': name,
                            'rank': REGEX_RANK})

    return sorted(matches, key=lambda x: x['rank'])

def _select_best_name_match(matches):
    """Returns the best name match of a ranked list of server_blocks.
    Adapted from the function of the same name in
    certbot_nginx.NginxConfigurator
    """
    if not matches:
        return None
    if matches[0]['rank'] in [START_WILDCARD_RANK, END_WILDCARD_RANK]:
        rank = matches[0]['rank']
        wildcards = [x for x in matches if x['rank'] == rank]
        return max(wildcards, key=lambda x: len(x['name']))['vhost']
    else:
        return matches[0]['vhost']

def choose_server_block(server_block_list, target_name):
    matches = _rank_matches_by_name(server_block_list, target_name)
    server_blocks = [x for x in [_select_best_name_match(matches)]
                     if x is not None]
    return server_blocks

