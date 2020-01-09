# Copyright 2019 VyOS maintainers and contributors <maintainers@vyos.io>
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

"""
Functions to define and read the VyOS configuration syntax version.

In order to support the syntax migration mechanism, configuration syntax is
versioned, by component, with the current versions stored in a JSON file. On
boot, before the migration mechanism is invoked, the current syntax versions
are updated with any packages that specify the appropriate entrypoint in the
package setup file.
"""

import os
import json
import logging

from typing import Dict
import entrypoints

import vyos.defaults

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SHARED_FILE = 'component-versions.json'
CONFIG_FILE = 'component.conf'

SHARED_PATH = os.path.join(vyos.defaults.directories['data'], SHARED_FILE)
CONFIG_PATH = os.path.join(vyos.defaults.directories['conf'], CONFIG_FILE)

def update_system_versions() -> None:
    """Load, update, and write the system component versions
    """

    vyos_conf_dir = os.path.join(vyos.defaults.directories['conf'])
    if not os.path.exists(vyos_conf_dir):
        os.mkdir(vyos_conf_dir)

    try:
        versions = _load_shared_data(SHARED_PATH)
        _update_version_data(versions)
        _write_config_data(versions, CONFIG_PATH)
    except Exception as err:
        logger.critical(f"update_system_versions failed !!! {err}")
        raise

def get_system_versions() -> Dict[str, int]:
    """Return system component versions
    """

    path: str = CONFIG_PATH
    component_versions: Dict[str, int] = {}

    try:
        with open(path, 'r') as f:
            component_versions = json.load(f)
    except Exception as err:
        logger.critical(f"Component data {path} is unavailable: {err}")

    return component_versions

def _load_shared_data(path: str) -> Dict[str, int]:
    """Load component versions from central file, or return empty dict
    """

    version_dict: Dict[str, int] = {}

    if os.path.isfile(path):
        with open(path, 'r') as f:
            try:
                version_dict = json.load(f)
            except ValueError as err:
                logger.critical(f"Component data {path} is not valid json:"
                                f" {err}")
                raise
    else:
        logger.debug(f"No component version data found in {path}")

    return version_dict

def _update_version_data(version_dict: Dict[str, int]) -> Dict[str, int]:
    """Update dictionary of component versions from packages

    Packages may define entrypoints to be included in config migration. This
    allows third-party, or experimental packages to be include in config
    migration. The entry_point should provide a Dict[str, int], with one or
    more entries: {'name': version, }.
    """

    for entry_point in entrypoints.get_group_all('vyos-component'):
        update = entry_point.load()
        if not isinstance(update, Dict):
            logger.error("Version info for {entry_point.name} is not dict")
            continue

        for k, v in update.items():
            if not isinstance(v, int):
                logger.error(f"Version value for {k} is not int")
                continue
            existing = version_dict.get(k)
            if existing is not None and v > existing:
                logger.info(f"Updating component version {k}: {v}")

            version_dict[k] = v

    return version_dict

def _write_config_data(version_dict: Dict[str, int], path: str) -> None:
    """Write component versions to be read during config migration
    """

    try:
        with open(path, 'w') as f:
            logger.debug(f"Writing component versions to {path}")
            json.dump(version_dict, f, indent=4, sort_keys=True)
    except Exception as err:
        logger.critical(f"Writing component versions {path} failed: {err}")
        raise

