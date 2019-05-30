#!/usr/bin/python3

import sys
import vyos.formatversions as formatversions
import vyos.systemversions as systemversions
import vyos.defaults
import vyos.version

sys_versions = systemversions.get_system_versions()

component_string = formatversions.format_versions_string(sys_versions)

os_version_string = vyos.version.get_version()

sys.stdout.write("\n\n")
if vyos.defaults.cfg_vintage == 'vyos':
    formatversions.write_vyos_versions_foot(None, component_string,
                                            os_version_string)
if vyos.defaults.cfg_vintage == 'vyatta':
    formatversions.write_vyatta_versions_foot(None, component_string,
                                              os_version_string)
