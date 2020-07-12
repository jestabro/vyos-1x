# Copyright 2020 VyOS maintainers and contributors <maintainers@vyos.io>
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
"""

from enum import IntFlag, auto

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.util import get_sub_dict
from vyos.xml import defaults

class ConfigDiffError(Exception):
    """
    Raised on config dict access errors, for example, calling get_value on
    a non-leaf node.
    """
    pass

def enum_to_key(e):
    return e.name.lower()

class Diff(IntFlag):
    MERGE = auto()
    DELETE = auto()
    ADD = auto()
    STABLE = auto()

requires_effective = enum_to_key(Diff.DELETE)
to_merge_defaults = enum_to_key(Diff.MERGE)

def _key_sets_from_dicts(session_dict, effective_dict):
    session_keys = list(session_dict)
    effective_keys = list(effective_dict)

    ret = {}
    stable_keys = [k for k in session_keys if k in effective_keys]

    ret[enum_to_key(Diff.STABLE)] = stable_keys
    ret[enum_to_key(Diff.ADD)] = [k for k in session_keys if k not in stable_keys]
    ret[enum_to_key(Diff.DELETE)] = [k for k in effective_keys if k not in stable_keys]
    ret[enum_to_key(Diff.MERGE)] = session_keys

    return ret

def _dict_from_key_set(key_set, d):
    # This will always be applied to a key_set obtained from a get_sub_dict,
    # hence there is no possibility of KeyError, as get_sub_dict guarantees
    # a return type of dict
    ret = {k: d[k] for k in key_set}

    return ret

def get_config_diff(config, key_mangling=None):
    """
    Check type and return ConfigDiff instance.
    """
    if not config or not isinstance(config, Config):
        raise TypeError("argument must me a Config instance")
    if key_mangling and not (isinstance(key_mangling, tuple) and \
            (len(key_mangling) == 2) and \
            isinstance(key_mangling[0], str) and \
            isinstance(key_mangling[1], str)):
        raise ValueError("key_mangling must be a tuple of two strings")

    return ConfigDiff(config, key_mangling)

class ConfigDiff(object):
    """
    The class of config changes as represented by comparison between the
    session config dict and the effective config dict.
    """
    def __init__(self, config, key_mangling=None):
        self._level = config.get_level()
        self._session_config_dict = config.get_config_dict(key_mangling=key_mangling)
        self._effective_config_dict = config.get_config_dict(effective=True,
                                                             key_mangling=key_mangling)

    def _make_path(self, path):
        # mirrored from Config; allow path arguments relative to level
        if isinstance(path, str):
            path = path.split()
        elif isinstance(path, list):
            pass
        else:
            raise TypeError("Path must be a whitespace-separated string or a list")

        ret = self._level + path
        return ret

    def set_level(self, path):
        """
        Set the *edit level*, that is, a relative config dict path.
        Once set, all operations will be relative to this path,
        for example, after ``set_level("system")``, calling
        ``get_value("name-server")`` is equivalent to calling
        ``get_value("system name-server")`` without ``set_level``.

        Args:
            path (str|list): relative config path
        """
        if isinstance(path, str):
            if path:
                self._level = path.split()
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
        ret = self._level.copy()
        return ret

    def get_child_nodes(self, path=[], expand_nodes=Diff(0), no_defaults=False):
        """
        Args:
            path (str|list): config path
            no_detaults=False: do not merge default values to ret['merge']

        Returns: dict of dicts, representing differences between session
                                and effective config, under path
                 dict['merge'] = session config values, merged with defaults, unless no_defaults
                 dict['delete'] = effective config values, not in session
                 dict['add'] = session config values, not in effective
                 dict['stable'] = config values in both session and effective
        """
        session_dict = get_sub_dict(self._session_config_dict,
                                    self._make_path(path), get_first_key=True)
        effective_dict = get_sub_dict(self._effective_config_dict,
                                      self._make_path(path), get_first_key=True)

        ret = _key_sets_from_dicts(session_dict, effective_dict)

        for e in Diff:
            if expand_nodes & e:
                k = enum_to_key(e)
                if k is requires_effective:
                    ret[k] = _dict_from_key_set(effective_dict, ret[k])
                else:
                    ret[k] = _dict_from_key_set(session_dict, ret[k])

                if k is to_merge_defaults and not no_defaults:
                    default_values = defaults(self._make_path(path))
                    print(f"JSE --- defaults: {default_values}")
                    ret[k] = dict_merge(default_values, ret[k])

        return ret

    # For illustration; in practice, one will likely want the full dict
    def child_nodes_changed(self, path=[]):
        ret = self.get_child_nodes(path)
        if not ret['add'] and not ret['delete']:
            return False
        return True

    def get_node(self, path=[], expand_nodes=Diff(0), no_defaults=False):
        """
        Args:
            path (str|list): config path
            no_detaults=False: do not merge default values to ret['merge']

        Returns: dict of dicts, representing differences between session
                                and effective config, under path
                 dict['merge'] = session config values, merged with defaults, unless no_defaults
                 dict['delete'] = effective config values, not in session
                 dict['add'] = session config values, not in effective
                 dict['stable'] = config values in both session and effective
        """
        session_dict = get_sub_dict(self._session_config_dict, self._make_path(path))
        effective_dict = get_sub_dict(self._effective_config_dict, self._make_path(path))

        ret = _key_sets_from_dicts(session_dict, effective_dict)

        for e in Diff:
            if expand_nodes & e:
                k = enum_to_key(e)
                if k is requires_effective:
                    ret[k] = _dict_from_key_set(effective_dict, ret[k])
                else:
                    ret[k] = _dict_from_key_set(session_dict, ret[k])

                if k is to_merge_defaults and not no_defaults:
                    default_values = defaults(self._make_path(path))
                    print(f"JSE --- defaults: {default_values}")
                    ret[k] = dict_merge(default_values, ret[k])

        return ret

    # For illustration; in practice, one will likely want the full dict
    def node_added(self, path=[]):
        ret = self.get_node(path)
        if not ret['add']:
            return False
        return True

    # For illustration; in practice, one will likely want the full dict
    def node_deleted(self, path=[]):
        ret = self.get_node(path)
        if not ret['delete']:
            return False
        return True

    def get_value(self, path=[]):
        """
        Args:
            path (str|list): config path

        Returns: (new, old) tuple of values in session config/effective config
        """
        # one should properly use is_leaf as check; for the moment we will
        # deduce from type, which will not catch call on non-leaf node if None
        new_value_dict = get_sub_dict(self._session_config_dict, self._make_path(path))
        old_value_dict = get_sub_dict(self._effective_config_dict, self._make_path(path))

        new_value = None
        old_value = None
        if new_value_dict:
            new_value = next(iter(new_value_dict.values()))
        if old_value_dict:
            old_value = next(iter(old_value_dict.values()))

        if new_value and isinstance(new_value, dict):
            raise ConfigDiffError("get_value_changed called on non-leaf node")
        if old_value and isinstance(old_value, dict):
            raise ConfigDiffError("get_value_changed called on non-leaf node")

        return new_value, old_value

    # For illustration; in practice, one will likely want the full dict
    def value_changed(self, path=[]):
        a, b = self.get_value(path)
        if a is b:
            return False
        return True

    # general purpose; similar form as Config.get_config_dict, though
    # key_mangling is defined on init
    def get_config_dict(self, path=[], effective=False, get_first_key=False):
        """
        Args:
            path (str|list): configuration tree path, can be empty
            effective=False: effective or session config
            get_first_key=False: if k = path[:-1], return sub-dict d[k] instead of {k: d[k]}

        Returns: a dict representation of the config under path
        """
        if effective:
            config_dict = self._effective_config_dict
        else:
            config_dict = self._session_config_dict

        config_dict = get_sub_dict(config_dict, self._make_path(path), get_first_key)

        return config_dict
