# Copyright 2023 VyOS maintainers and contributors <maintainers@vyos.io>
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
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from pathlib import Path
from re import compile, MULTILINE, DOTALL

from vyos.system import disk, grub, image, MOD_CFG_VER
from vyos.template import render

TMPL_GRUB_COMPAT: str = 'grub/grub_compat.j2'

# define regexes and variables
REGEX_VERSION = r'^menuentry "[^\n]*{\n[^}]*\s+linux /boot/(?P<version>\S+)/[^}]*}'
REGEX_MENUENTRY = r'^menuentry "[^\n]*{\n[^}]*\s+linux /boot/(?P<version>\S+)/vmlinuz (?P<options>[^\n]+)\n[^}]*}'
REGEX_CONSOLE = r'^.*console=(?P<console_type>[^\s\d]+)(?P<console_num>[\d]+).*$'
REGEX_SANIT_CONSOLE = r'\ ?console=[^\s\d]+[\d]+(,\d+)?\ ?'
REGEX_SANIT_INIT = r'\ ?init=\S*\ ?'
PW_RESET_OPTION = 'init=/opt/vyatta/sbin/standalone_root_pw_reset'

def in_compat_mode():
    if grub.get_cfg_ver() >= MOD_CFG_VER:
        return False

    return True

def find_versions(menu_entries: list) -> list:
    """Find unique VyOS versions from menu entries

    Args:
        menu_entries (list): a list with menu entries

    Returns:
        list: List of installed versions
    """
    versions = []
    for vyos_ver in menu_entries:
        versions.append(vyos_ver.get('version'))
    # remove duplicates
    versions = list(set(versions))
    return versions


def filter_unparsed(grub_path: str) -> str:
    """Find currently installed VyOS version

    Args:
        grub_path (str): a path to the grub.cfg file

    Returns:
        str: unparsed grub.cfg items
    """
    config_text = Path(grub_path).read_text()
    regex_filter = compile(REGEX_VERSION, MULTILINE | DOTALL)
    filtered = regex_filter.sub('', config_text)
    regex_filter = compile(grub.REGEX_GRUB_VARS, MULTILINE)
    filtered = regex_filter.sub('', filtered)
    regex_filter = compile(grub.REGEX_GRUB_MODULES, MULTILINE)
    filtered = regex_filter.sub('', filtered)
    # strip extra new lines
    filtered = filtered.strip()
    return filtered


def sanitize_boot_opts(boot_opts: str) -> str:
    """Sanitize boot options from console and init

    Args:
        boot_opts (str): boot options

    Returns:
        str: sanitized boot options
    """
    regex_filter = compile(REGEX_SANIT_CONSOLE)
    boot_opts = regex_filter.sub('', boot_opts)
    regex_filter = compile(REGEX_SANIT_INIT)
    boot_opts = regex_filter.sub('', boot_opts)

    return boot_opts


def parse_entry(entry: tuple) -> dict:
    """Parse GRUB menuentry

    Args:
        entry (tuple): tuple of (version, options)

    Returns:
        dict: dictionary with parsed options
    """
    # save version to dict
    entry_dict = {'version': entry[0]}
    # detect boot mode type
    if PW_RESET_OPTION in entry[1]:
        entry_dict['bootmode'] = 'pw_reset'
    else:
        entry_dict['bootmode'] = 'normal'
    # find console type and number
    regex_filter = compile(REGEX_CONSOLE)
    entry_dict.update(regex_filter.match(entry[1]).groupdict())
    entry_dict['boot_opts'] = sanitize_boot_opts(entry[1])

    return entry_dict


def parse_menuntries(grub_path: str) -> list:
    """Parse all GRUB menuentries

    Args:
        grub_path (str): a path to GRUB config file

    Returns:
        list: list with menu items (each item is a dict)
    """
    menuentries = []
    # read configuration file
    config_text = Path(grub_path).read_text()
    # parse menuentries to tuples (version, options)
    regex_filter = compile(REGEX_MENUENTRY, MULTILINE)
    filter_results = regex_filter.findall(config_text)
    # parse each entry
    for entry in filter_results:
        menuentries.append(parse_entry(entry))

    return menuentries

def update_cfg_version():
    images_details = image.get_images_details()
    cfg_version = min(d['module_version'] for d in images_details)

    return cfg_version

def update_version_list() -> list[str]:
    """Update list of installed VyOS versions for rendering

    Returns:
        list: list of installed VyOS versions
    """
    # find root directory of persistent storage
    root_dir = disk.find_persistence()
    grub_cfg_main = f'{root_dir}/{grub.GRUB_CFG_MAIN}'
    # get list of versions in menuentries
    menu_entries = parse_menuntries(grub_cfg_main)
    menu_versions = find_versions(menu_entries)
    # get list of versions added by new or legacy tools
    current_versions = grub.version_list(root_dir)
    # differences should be <= 1, as legacy grub.cfg will be updated on each
    # add_image/delete_image
    diff = list(set(current_versions) - set(menu_versions))
    for ver in diff:
        last_version = menu_entries[0].get('version')
        add_block = list(filter(lambda x: x.get('version') == last_version,
                                menu_entries))
        for e in add_block:
            e.update({'version': ver})
        menu_entries = add_block + menu_entries

    diff = list(set(menu_versions) - set(current_versions))
    for ver in diff:
        menu_entries = list(filter(lambda x: x.get('version') != ver,
                                   menu_entries))

    return menu_entries


def grub_cfg_details() -> dict:
    """Gather details for compatibility mode"""
    # find root directory of persistent storage
    root_dir = disk.find_persistence()

    details = {}
    details |= grub.vars_read(f'{root_dir}/{grub.CFG_VYOS_VARS}')
    details |= grub.vars_read(f'{root_dir}/{grub.GRUB_CFG_MAIN}')
    details['versions'] = update_version_list()
    details['tools_version'] = MOD_CFG_VER

    p = Path('/sys/firmware/efi')
    if p.is_dir():
        details['efi'] = True
    else:
        details['efi'] = False

    return details

def render_grub_cfg(target):
    render(target, TMPL_GRUB_COMPAT, grub_cfg_details())
