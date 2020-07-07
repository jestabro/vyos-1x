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

from vyos.config import Config
from vyos.util import get_sub_dict, mangle_dict_keys

class ConfigDiffError(Exception):
    """
    """
    pass

def get_config_diff(config):
    if not config or not isinstance(config, Config):
        raise TypeError("argument must me a Config instance")
    return ConfigDiff(config)

def _key_sets_from_dicts(session_dict, effective_dict):
    session_keys = list(session_dict)
    effective_keys = list(effective_dict)

    stable_keys = [k for k in session_keys if k in effective_keys]
    added_keys = [k for k in session_keys if k not in stable_keys]
    deleted_keys = [k for k in effective_keys if k not in stable_keys]

    return added_keys, deleted_keys, stable_keys

def _dict_from_key_set(d, key_set):
    # This will always be applied to a key_set obtained from a get_sub_dict,
    # hence there is no possibility of KeyError, as get_sub_dict guarantees
    # a return type of dict
    ret = {k: d[k] for k in key_set}
    return ret

def _mangle_dict_keys(d, key_mangling):
    if not (isinstance(key_mangling, tuple) and \
            (len(key_mangling) == 2) and \
            isinstance(key_mangling[0], str) and \
            isinstance(key_mangling[1], str)):
        raise ValueError("key_mangling must be a tuple of two strings")
    else:
        d = mangle_dict_keys(d, key_mangling[0], key_mangling[1])
        return d

class ConfigDiff(object):
    """
    """
    def __init__(self, config):
        self._level = config.get_level()
        self._session_config_dict = config.get_config_dict()
        self._effective_config_dict = config.get_config_dict(effective=True)

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

    def get_child_nodes_changed(self, path=[], return_as_dict=False, key_mangling=None):
        session_dict = get_sub_dict(self._session_config_dict, self._make_path(path), get_first_key=True)
        effective_dict = get_sub_dict(self._effective_config_dict, self._make_path(path), get_first_key=True)

        added_keys, deleted_keys, _ = _key_sets_from_dicts(session_dict, effective_dict)

        if not return_as_dict:
            return added_keys, deleted_keys

        added_dict = _dict_from_key_set(session_dict, added_keys)
        deleted_dict = _dict_from_key_set(effective_dict, deleted_keys)
        if key_mangling:
            added_dict = _mangle_dict_keys(added_dict, key_mangling)
            deleted_dict = _mangle_dict_keys(deleted_dict, key_mangling)

        return added_dict, deleted_dict

    def get_child_nodes_unchanged(self, path=[], return_as_dict=False, key_mangling=None):
        session_dict = get_sub_dict(self._session_config_dict, self._make_path(path), get_first_key=True)
        effective_dict = get_sub_dict(self._effective_config_dict, self._make_path(path), get_first_key=True)

        _, _, stable_keys = _key_sets_from_dicts(session_dict, effective_dict)

        if not return_as_dict:
            return stable_keys

        stable_dict = _dict_from_key_set(session_dict, stable_keys)
        if key_mangling:
            stable_dict = _mangle_dict_keys(stable_dict, key_mangling)

        return stable_dict

    def child_nodes_changed(self, path=[]):
        a, b = self.get_child_nodes_changed(path)
        if not a and not b:
            return False
        return True

    def get_node_changed(self, path=[], return_as_dict=False, key_mangling=None):
        session_dict = get_sub_dict(self._session_config_dict, self._make_path(path))
        effective_dict = get_sub_dict(self._effective_config_dict, self._make_path(path))

        added_key, deleted_key, _ = _key_sets_from_dicts(session_dict, effective_dict)
        if not return_as_dict:
            return added_key, deleted_key

        added_dict = _dict_from_key_set(session_dict, added_key)
        deleted_dict = _dict_from_key_set(effective_dict, deleted_key)
        if key_mangling:
            added_dict = _mangle_dict_keys(added_dict, key_mangling)
            deleted_dict = _mangle_dict_keys(deleted_dict, key_mangling)

        return added_dict, deleted_dict

    def get_node_unchanged(self, path=[], return_as_dict=False, key_mangling=None):
        session_dict = get_sub_dict(self._session_config_dict, self._make_path(path))
        effective_dict = get_sub_dict(self._effective_config_dict, self._make_path(path))

        _, _, stable_key = _key_sets_from_dicts(session_dict, effective_dict)

        if not return_as_dict:
            return stable_key

        stable_dict = _dict_from_key_set(session_dict, stable_key)
        if key_mangling:
            stable_dict = _mangle_dict_keys(stable_dict, key_mangling)

        return stable_dict

    def node_added(self, path=[]):
        a, _ = self.get_node_changed(path)
        if not a:
            return False
        return True

    def node_deleted(self, path=[]):
        _, b = self.get_node_changed(path)
        if not b:
            return False
        return True

    def get_value(self, path=[]):
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

    def value_changed(self, path=[]):
        a, b = self.get_value(path)
        if a is b:
            return False
        return True

    # general purpose; same form as Config.get_config_dict
    def get_config_dict(self, path=[], effective=False, key_mangling=None, get_first_key=False):
        if effective:
            config_dict = self._effective_config_dict
        else:
            config_dict = self._session_config_dict

        config_dict = get_sub_dict(config_dict, self._make_path(path), get_first_key)
        if key_mangling:
            config_dict = _mangle_dict_keys(config_dict, key_mangling)

        return config_dict
