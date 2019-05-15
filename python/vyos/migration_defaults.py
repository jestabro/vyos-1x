import os

vyatta_config_migrate_dir = '/opt/vyatta/etc/config-migrate'
vyatta_migrate_script_dir = os.path.join(vyatta_config_migrate_dir, 'migrate')
vyatta_system_version_dir = os.path.join(vyatta_config_migrate_dir, 'current')
default_vintage = 'vyatta'

