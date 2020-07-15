# Copyright 2017, 2019 VyOS maintainers and contributors <maintainers@vyos.io>
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
A library for reading VyOS running config data.

This library is used internally by all config scripts of VyOS,
but its API should be considered stable and safe to use
in user scripts.

Note that this module will not work outside VyOS.

Node taxonomy
#############

There are multiple types of config tree nodes in VyOS, each requires
its own set of operations.

*Leaf nodes* (such as "address" in interfaces) can have values, but cannot
have children. 
Leaf nodes can have one value, multiple values, or no values at all.

For example, "system host-name" is a single-value leaf node,
"system name-server" is a multi-value leaf node (commonly abbreviated "multi node"),
and "system ip disable-forwarding" is a valueless leaf node.

Non-leaf nodes cannot have values, but they can have child nodes. They are divided into
two classes depending on whether the names of their children are fixed or not.
For example, under "system", the names of all valid child nodes are predefined
("login", "name-server" etc.).

To the contrary, children of the "system task-scheduler task" node can have arbitrary names.
Such nodes are called *tag nodes*. This terminology is confusing but we keep using it for lack
of a better word. No one remembers if the "tag" in "task Foo" is "task" or "Foo",
but the distinction is irrelevant in practice.

Configuration modes
###################

VyOS has two distinct modes: operational mode and configuration mode. When a user logins,
the CLI is in the operational mode. In this mode, only the running (effective) config is accessible for reading.

When a user enters the "configure" command, a configuration session is setup. Every config session
has its *proposed* (or *session*) config built on top of the current running config. When changes are commited, if commit succeeds,
the proposed config is merged into the running config.

In configuration mode, "base" functions like `exists`, `return_value` return values from the session config,
while functions prefixed "effective" return values from the running config.

In operational mode, all functions return values from the running config.

"""

import re
import json

import vyos.util
import vyos.configtree
from vyos.configsource import ConfigSource, ConfigSourceSession

class Config(object):
    """
    The class of config access objects.

    Internally, in the current implementation, this object is *almost* stateless,
    the only state it keeps is relative *config path* for convenient access to config
    subtrees.
    """
    def __init__(self, session_env=None, config_source=None):
        if config_source is None:
            self._config_source = ConfigSourceSession(session_env)
        else:
            if not isinstance(config_source, ConfigSource):
                raise TypeError("config_source not of type ConfigSource")
            self._config_source = config_source

        self._level = []
        (self._running_config,
         self._session_config) = self._config_source.get_configtree_tuple()

    def _make_path(self, path):
        # Backwards-compatibility stuff: original implementation used string paths
        # libvyosconfig paths are lists, but since node names cannot contain whitespace,
        # splitting at whitespace is reasonably safe.
        # It may cause problems with exists() when it's used for checking values,
        # since values may contain whitespace.
        if isinstance(path, str):
            path = re.split(r'\s+', path)
        elif isinstance(path, list):
            pass
        else:
            raise TypeError("Path must be a whitespace-separated string or a list")
        return (self._level + path)

    def set_level(self, path):
        """
        Set the *edit level*, that is, a relative config tree path.
        Once set, all operations will be relative to this path,
        for example, after ``set_level("system")``, calling
        ``exists("name-server")`` is equivalent to calling
        ``exists("system name-server"`` without ``set_level``.

        Args:
            path (str|list): relative config path
        """
        # Make sure there's always a space between default path (level)
        # and path supplied as method argument
        # XXX: for small strings in-place concatenation is not a problem
        if isinstance(path, str):
            if path:
                self._level = re.split(r'\s+', path)
            else:
                self._level = []
        elif isinstance(path, list):
            self._level = path.copy()
        else:
            raise TypeError("Level path must be either a whitespace-separated string or a list")

    def get_level(self):
        """
        Gets the current edit level.

        Returns:
            str: current edit level
        """
        return(self._level.copy())

    def exists(self, path):
        """
        Checks if a node with given path exists in the running or proposed config

        Returns:
            True if node exists, False otherwise

        Note:
            This function cannot be used outside a configuration sessions.
            In operational mode scripts, use ``exists_effective``.
        """
        if not self._session_config:
            return False
        if self._session_config.exists(self._make_path(path)):
            return True
        else:
            # libvyosconfig exists() works only for _nodes_, not _values_
            # libvyattacfg one also worked for values, so we emulate that case here
            if isinstance(path, str):
                path = re.split(r'\s+', path)
            path_without_value = path[:-1]
            path_str = " ".join(path_without_value)
            try:
                value = self._session_config.return_value(self._make_path(path_str))
                return (value == path[-1])
            except vyos.configtree.ConfigTreeError:
                # node doesn't exist at all
                return False

    def session_changed(self):
        """
        Returns:
            True if the config session has uncommited changes, False otherwise.
        """
        if isinstance(self._config_source, ConfigSourceSession):
            return self._config_source.session_changed()
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def in_session(self):
        """
        Returns:
            True if called from a configuration session, False otherwise.
        """
        if isinstance(self._config_source, ConfigSourceSession):
            return self._config_source.in_session()
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def show_config(self, path=[], default=None, effective=False):
        """
        Args:
            path (str list): Configuration tree path, or empty
            default (str): Default value to return

        Returns:
            str: working configuration
        """
        if isinstance(self._config_source, ConfigSourceSession):
            return self._config_source.show_config(path, default, effective)
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def get_cached_dict(self, effective=False):
        cached = self._dict_cache.get(effective, {})
        if cached:
            config_dict = cached
        else:
            config_dict = {}

            if effective:
                if self._running_config:
                    config_dict = json.loads((self._running_config).to_json())
            else:
                if self._session_config:
                    config_dict = json.loads((self._session_config).to_json())

            self._dict_cache[effective] = config_dict

        return config_dict

    def get_config_dict(self, path=[], effective=False, key_mangling=None, get_first_key=False):
        """
        Args:
            path (str list): Configuration tree path, can be empty
            effective=False: effective or session config
            key_mangling=None: mangle dict keys according to regex and replacement
            get_first_key=False: if k = path[:-1], return sub-dict d[k] instead of {k: d[k]}

        Returns: a dict representation of the config under path
        """
        config_dict = self.get_cached_dict(effective)

        config_dict = vyos.util.get_sub_dict(config_dict, self._make_path(path), get_first_key)

        if key_mangling:
            if not (isinstance(key_mangling, tuple) and \
                    (len(key_mangling) == 2) and \
                    isinstance(key_mangling[0], str) and \
                    isinstance(key_mangling[1], str)):
                raise ValueError("key_mangling must be a tuple of two strings")
            else:
                config_dict = vyos.util.mangle_dict_keys(config_dict, key_mangling[0], key_mangling[1])
        else:
            config_dict = deepcopy(config_dict)

        return config_dict

    def is_multi(self, path):
        """
        Args:
            path (str): Configuration tree path

        Returns:
            True if a node can have multiple values, False otherwise.

        Note:
            It also returns False if node doesn't exist.
        """
        if isinstance(self._config_source, ConfigSourceSession):
            self._config_source.set_level(self.get_level)
            return self._config_source.is_multi(path)
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def is_tag(self, path):
        """
         Args:
            path (str): Configuration tree path

        Returns:
            True if a node is a tag node, False otherwise.

        Note:
            It also returns False if node doesn't exist.
        """
        if isinstance(self._config_source, ConfigSourceSession):
            self._config_source.set_level(self.get_level)
            return self._config_source.is_tag(path)
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def is_leaf(self, path):
        """
         Args:
            path (str): Configuration tree path

        Returns:
            True if a node is a leaf node, False otherwise.

        Note:
            It also returns False if node doesn't exist.
        """
        if isinstance(self._config_source, ConfigSourceSession):
            self._config_source.set_level(self.get_level)
            return self._config_source.is_leaf(path)
        else:
            raise TypeError(f"function not available for {type(self._config_source)}")

    def return_value(self, path, default=None):
        """
        Retrieve a value of single-value leaf node in the running or proposed config

        Args:
            path (str): Configuration tree path
            default (str): Default value to return if node does not exist

        Returns:
            str: Node value, if it has any
            None: if node is valueless *or* if it doesn't exist

        Note:
            Due to the issue with treatment of valueless nodes by this function,
            valueless nodes should be checked with ``exists`` instead.

            This function cannot be used outside a configuration session.
            In operational mode scripts, use ``return_effective_value``.
        """
        if self._session_config:
            try:
                value = self._session_config.return_value(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                value = None
        else:
            value = None

        if not value:
            return(default)
        else:
            return(value)

    def return_values(self, path, default=[]):
        """
        Retrieve all values of a multi-value leaf node in the running or proposed config

        Args:
            path (str): Configuration tree path

        Returns:
            str list: Node values, if it has any
            []: if node does not exist

        Note:
            This function cannot be used outside a configuration session.
            In operational mode scripts, use ``return_effective_values``.
        """
        if self._session_config:
            try:
                values = self._session_config.return_values(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                values = []
        else:
            values = []

        if not values:
            return(default.copy())
        else:
            return(values)

    def list_nodes(self, path, default=[]):
        """
        Retrieve names of all children of a tag node in the running or proposed config

        Args:
            path (str): Configuration tree path

        Returns:
            string list: child node names

        """
        if self._session_config:
            try:
                nodes = self._session_config.list_nodes(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                nodes = []
        else:
            nodes = []

        if not nodes:
            return(default.copy())
        else:
            return(nodes)

    def exists_effective(self, path):
        """
        Check if a node exists in the running (effective) config

        Args:
            path (str): Configuration tree path

        Returns:
            True if node exists in the running config, False otherwise

        Note:
            This function is safe to use in operational mode. In configuration mode,
            it ignores uncommited changes.
        """
        if self._running_config:
            return(self._running_config.exists(self._make_path(path)))

        return False

    def return_effective_value(self, path, default=None):
        """
        Retrieve a values of a single-value leaf node in a running (effective) config

        Args:
            path (str): Configuration tree path
            default (str): Default value to return if node does not exist

        Returns:
            str: Node value
        """
        if self._running_config:
            try:
                value = self._running_config.return_value(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                value = None
        else:
            value = None

        if not value:
            return(default)
        else:
            return(value)

    def return_effective_values(self, path, default=[]):
        """
        Retrieve all values of a multi-value node in a running (effective) config

        Args:
            path (str): Configuration tree path

        Returns:
            str list: A list of values
        """
        if self._running_config:
            try:
                values = self._running_config.return_values(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                values = []
        else:
            values = []

        if not values:
            return(default.copy())
        else:
            return(values)

    def list_effective_nodes(self, path, default=[]):
        """
        Retrieve names of all children of a tag node in the running config

        Args:
            path (str): Configuration tree path

        Returns:
            str list: child node names
        """
        if self._running_config:
            try:
                nodes = self._running_config.list_nodes(self._make_path(path))
            except vyos.configtree.ConfigTreeError:
                nodes = []
        else:
            nodes = []

        if not nodes:
            return(default.copy())
        else:
            return(nodes)
