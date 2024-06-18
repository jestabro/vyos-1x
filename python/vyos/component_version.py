# Copyright 2022-2024 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions for reading/writing component versions.

The config file version string has the following form:

VyOS 1.3/1.4:

// Warning: Do not remove the following line.
// vyos-config-version: "broadcast-relay@1:cluster@1:config-management@1:conntrack@3:conntrack-sync@2:dhcp-relay@2:dhcp-server@6:dhcpv6-server@1:dns-forwarding@3:firewall@5:https@2:interfaces@22:ipoe-server@1:ipsec@5:isis@1:l2tp@3:lldp@1:mdns@1:nat@5:ntp@1:pppoe-server@5:pptp@2:qos@1:quagga@8:rpki@1:salt@1:snmp@2:ssh@2:sstp@3:system@21:vrrp@2:vyos-accel-ppp@2:wanloadbalance@3:webproxy@2:zone-policy@1"
// Release version: 1.3.0

VyOS 1.2:

/* Warning: Do not remove the following line. */
/* === vyatta-config-version: "broadcast-relay@1:cluster@1:config-management@1:conntrack-sync@1:conntrack@1:dhcp-relay@2:dhcp-server@5:dns-forwarding@1:firewall@5:ipsec@5:l2tp@1:mdns@1:nat@4:ntp@1:pppoe-server@2:pptp@1:qos@1:quagga@7:snmp@1:ssh@1:system@10:vrrp@2:wanloadbalance@3:webgui@1:webproxy@2:zone-policy@1" === */
/* Release version: 1.2.8 */

"""

import os
import re
import sys
import fileinput
from dataclasses import dataclass
from dataclasses import replace
from typing import Optional

from vyos.xml_ref import component_version
from vyos.version import get_version
from vyos.defaults import directories

DEFAULT_CONFIG_PATH = os.path.join(directories['config'], 'config.boot')

REGEX_WARN_VYOS = r'(// Warning: Do not remove the following line.)'
REGEX_WARN_VYATTA = r'(/\* Warning: Do not remove the following line. \*/)'
REGEX_COMPONENT_VERSION_VYOS = r'// vyos-config-version:\s+"([\w@:-]+)"\s*'
REGEX_COMPONENT_VERSION_VYATTA = r'/\* === vyatta-config-version:\s+"([\w@:-]+)"\s+=== \*/'
REGEX_RELEASE_VERSION_VYOS = r'// Release version:\s+(\S*)\s*'
REGEX_RELEASE_VERSION_VYATTA = r'/\* Release version:\s+(\S*)\s*\*/'

CONFIG_FILE_VERSION = """\
// Warning: Do not remove the following line.
// vyos-config-version: "{}"
// Release version: {}
"""

warn_filter_vyos = re.compile(REGEX_WARN_VYOS)
warn_filter_vyatta = re.compile(REGEX_WARN_VYATTA)

regex_filter = { 'vyos': dict(zip(['component', 'release'],
                                  [re.compile(REGEX_COMPONENT_VERSION_VYOS),
                                   re.compile(REGEX_RELEASE_VERSION_VYOS)])),
                 'vyatta': dict(zip(['component', 'release'],
                                    [re.compile(REGEX_COMPONENT_VERSION_VYATTA),
                                     re.compile(REGEX_RELEASE_VERSION_VYATTA)])) }

@dataclass
class VersionInfo:
    component: Optional[dict[str,int]] = None
    release: str = get_version()
    vintage: str = 'vyos'
    config_body: Optional[str] = None
    footer_lines: Optional[list[str]] = None

    def component_is_none(self) -> bool:
        return bool(self.component is None)

    def config_body_is_none(self) -> bool:
        return bool(self.config_body is None)

    def update_footer(self):
        f = CONFIG_FILE_VERSION.format(component_to_string(self.component),
                                       self.release)
        self.footer_lines = f.splitlines()

    def update_syntax(self):
        self.vintage = 'vyos'
        self.update_footer()

    def update_release(self, release: str):
        self.release = release
        self.update_footer()

    def update_component(self, key: str, version: int):
        if not isinstance(version, int):
            raise ValueError('version must be int')
        if self.component is None:
            self.component = {}
        self.component[key] = version
        self.update_footer()

    def update_config_body(self, config_str: str):
        self.config_body = config_str

    def write(self, config_file) -> bool:
        if self.config_body is None or self.footer_lines is None:
            return False
        try:
            with open(config_file, 'w') as f:
                f.write(self.config_body + '\n' + '\n'.join(self.footer_lines))
        except OSError:
            return False
        return True

def component_to_string(component: dict) -> str:
    l = [f'{k}@{v}' for k, v in sorted(component.items(), key=lambda x: x[0])]
    return ':'.join(l)

def component_from_string(string: str) -> dict:
    return {k: int(v) for k, v in re.findall(r'([\w,-]+)@(\d+)', string)}

def version_info_from_file(config_file) -> VersionInfo:
    version_info = VersionInfo()
    try:
        with open(config_file) as f:
            config_str = f.read()
    except OSError:
        return None

    if len(parts := warn_filter_vyos.split(config_str)) > 1:
        vintage = 'vyos'
    elif len(parts := warn_filter_vyatta.split(config_str)) > 1:
        vintage = 'vyatta'
    else:
        version_info.config_body = parts[0] if parts else None
        return version_info

    version_info.vintage = vintage
    version_info.config_body = parts[0]
    version_lines = ''.join(parts[1:]).splitlines()
    if len(version_lines) != 3:
        raise ValueError(f'Malformed version strings: {version_lines}')

    m = regex_filter[vintage]['component'].match(version_lines[1])
    if not m:
        raise ValueError(f'Malformed component string: {version_lines[1]}')
    version_info.component = component_from_string(m.group(1))

    m = regex_filter[vintage]['release'].match(version_lines[2])
    if not m:
        raise ValueError(f'Malformed component string: {version_lines[2]}')
    version_info.release = m.group(1)

    version_info.footer_lines = version_lines

    return version_info

def version_info_from_system() -> VersionInfo:
    """
    Return system component versions.
    """
    version_info = VersionInfo(
        component = component_version(),
        release =  get_version(),
        vintage = 'vyos'
    )

    return version_info

def version_info_copy(v: VersionInfo) -> VersionInfo:
    return replace(v)

def from_string(string_line, vintage='vyos'):
    """
    Get component version dictionary from string.
    Return empty dictionary if string contains no config information
    or raise error if component version string malformed.
    """
    version_dict = {}

    if vintage == 'vyos':
        if re.match(r'// vyos-config-version:.+', string_line):
            if not re.match(r'// vyos-config-version:\s+"([\w,-]+@\d+:)+([\w,-]+@\d+)"\s*', string_line):
                raise ValueError(f"malformed configuration string: {string_line}")

            for pair in re.findall(r'([\w,-]+)@(\d+)', string_line):
                version_dict[pair[0]] = int(pair[1])

    elif vintage == 'vyatta':
        if re.match(r'/\* === vyatta-config-version:.+=== \*/$', string_line):
            if not re.match(r'/\* === vyatta-config-version:\s+"([\w,-]+@\d+:)+([\w,-]+@\d+)"\s+=== \*/$', string_line):
                raise ValueError(f"malformed configuration string: {string_line}")

            for pair in re.findall(r'([\w,-]+)@(\d+)', string_line):
                version_dict[pair[0]] = int(pair[1])
    else:
        raise ValueError("Unknown config string vintage")

    return version_dict

def from_file(config_file_name=DEFAULT_CONFIG_PATH, vintage='vyos'):
    """
    Get component version dictionary parsing config file line by line
    """
    with open(config_file_name, 'r') as f:
        for line_in_config in f:
            version_dict = from_string(line_in_config, vintage=vintage)
            if version_dict:
                return version_dict

    # no version information
    return {}

def from_system():
    """
    Get system component version dict.
    """
    return component_version()

def format_string(ver: dict) -> str:
    """
    Version dict to string.
    """
    keys = list(ver)
    keys.sort()
    l = []
    for k in keys:
        v = ver[k]
        l.append(f'{k}@{v}')
    sep = ':'
    return sep.join(l)

def version_footer(ver: dict, vintage='vyos') -> str:
    """
    Version footer as string.
    """
    ver_str = format_string(ver)
    release = get_version()
    if vintage == 'vyos':
        ret_str = (f'// Warning: Do not remove the following line.\n'
                +  f'// vyos-config-version: "{ver_str}"\n'
                +  f'// Release version: {release}\n')
    elif vintage == 'vyatta':
        ret_str = (f'/* Warning: Do not remove the following line. */\n'
                +  f'/* === vyatta-config-version: "{ver_str}" === */\n'
                +  f'/* Release version: {release} */\n')
    else:
        raise ValueError("Unknown config string vintage")

    return ret_str

def system_footer(vintage='vyos') -> str:
    """
    System version footer as string.
    """
    ver_d = from_system()
    return version_footer(ver_d, vintage=vintage)

def write_version_footer(ver: dict, file_name, vintage='vyos'):
    """
    Write version footer to file.
    """
    footer = version_footer(ver=ver, vintage=vintage)
    if file_name:
        with open(file_name, 'a') as f:
            f.write(footer)
    else:
        sys.stdout.write(footer)

def write_system_footer(file_name, vintage='vyos'):
    """
    Write system version footer to file.
    """
    ver_d = from_system()
    return write_version_footer(ver_d, file_name=file_name, vintage=vintage)

def remove_footer(file_name):
    """
    Remove old version footer.
    """
    for line in fileinput.input(file_name, inplace=True):
        if re.match(r'/\* Warning:.+ \*/$', line):
            continue
        if re.match(r'/\* === vyatta-config-version:.+=== \*/$', line):
            continue
        if re.match(r'/\* Release version:.+ \*/$', line):
            continue
        if re.match('// vyos-config-version:.+', line):
            continue
        if re.match('// Warning:.+', line):
            continue
        if re.match('// Release version:.+', line):
            continue
        sys.stdout.write(line)
