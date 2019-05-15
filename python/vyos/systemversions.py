import os
import re
import sys
import vyos.migration_defaults

def get_system_versions():
    """
    Get component versions from running system; critical failure if
    unable to read migration directory.
    """
    system_versions = {}

    try:
        version_info = os.listdir(
                vyos.migration_defaults.vyatta_system_version_dir)
    except OSError as err:
        print("OS error: {}".format(err))
        sys.exit(1)

    for info in version_info:
        if re.match(r'[\w,-]+@\d+', info):
            pair = info.split('@')
            system_versions[pair[0]] = int(pair[1])

    return system_versions
