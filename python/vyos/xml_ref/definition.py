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

from typing import Union, Optional, Any
from vyos.configdict import dict_merge

class Xml:
    def __init__(self):
        self.ref = {}

    def define(self, ref: dict):
        self.ref = ref

    def _get_ref_node_data(self, node: dict, data: str) -> Union[bool, str]:
        res = node.get('node_data', {})
        if not res:
            raise ValueError("non-existent node data")
        if data not in res:
            raise ValueError("non-existent data field")

        return res.get(data)

    def _get_ref_path(self, path: list) -> dict:
        ref_path = path.copy()
        d = self.ref
        while ref_path and d:
            d = d.get(ref_path[0], {})
            ref_path.pop(0)
            if self._is_tag_node(d) and ref_path:
                ref_path.pop(0)

        return d

    def _is_tag_node(self, node: dict) -> bool:
        res = self._get_ref_node_data(node, 'node_type')
        return res == 'tag'

    def is_tag(self, path: list) -> bool:
        ref_path = path.copy()
        d = self.ref
        while ref_path and d:
            d = d.get(ref_path[0], {})
            ref_path.pop(0)
            if self._is_tag_node(d) and ref_path:
                if len(ref_path) == 1:
                    return False
                ref_path.pop(0)

        return self._is_tag_node(d)

    def is_tag_value(self, path: list) -> bool:
        if len(path) < 2:
            return False

        return self.is_tag(path[:-1])

    def _is_multi_node(self, node: dict) -> bool:
        b = self._get_ref_node_data(node, 'multi')
        assert isinstance(b, bool)
        return b

    def is_multi(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return  self._is_multi_node(d)

    def _is_valueless_node(self, node: dict) -> bool:
        b = self._get_ref_node_data(node, 'valueless')
        assert isinstance(b, bool)
        return b

    def is_valueless(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return  self._is_valueless_node(d)

    def _is_leaf_node(self, node: dict) -> bool:
        res = self._get_ref_node_data(node, 'node_type')
        return res == 'leaf'

    def is_leaf(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return self._is_leaf_node(d)

    def multi_to_list(self, rpath: list, conf: dict):
        if rpath and rpath[-1] in list(conf):
            raise ValueError('rpath should be disjoint from conf keys')

        for k in list(conf):
            d = self._get_ref_path(rpath + [k])
            if self._is_leaf_node(d):
                if self._is_multi_node(d) and not isinstance(conf[k], list):
                    conf[k] = [conf[k]]
            else:
                self.multi_to_list(rpath + [k], conf[k])

    def _get_default_value(self, node: dict):
        return self._get_ref_node_data(node, "default_value")

    def get_defaults(self, path: list, get_first_key=False) -> dict:
        """Return dict containing default values below path

        Note that descent below path will not proceed beyond an encountered
        tag node, as no tag node value is known. For a default dict relative
        to an existing config dict containing tag node values, see function:
        'relative_defaults'
        """
        res: Any = {}
        d = self._get_ref_path(path)
        if self._is_leaf_node(d):
            default_value = self._get_default_value(d)
            if default_value is not None:
                res = default_value
                if self._is_multi_node(d) and not isinstance(res, list):
                    res = [res]
        elif self.is_tag(path):
            # tag node defaults are used as suggestion, not default value;
            # should this change, append to path and continue recursion
            pass
        else:
            for k in list(d):
                if k == 'node_data':
                    continue
                pos = self.get_defaults(path + [k])
                res |= pos
        if res:
            if get_first_key or not path:
                if not isinstance(res, dict):
                    raise TypeError("Cannot get_first_key as data under node is not of type dict")
                return res
            return {path[-1]: res}

        return {}

    def relative_defaults(self, rpath: list, conf: Optional[dict] = None,
                          get_first_key=False) -> dict:
        if conf is None:
            conf = {}
        if rpath and rpath[-1] in list(conf):
            raise ValueError('rpath should be disjoint from conf keys')
        res: Any = {}
        d = self._get_ref_path(rpath)
        if self._is_leaf_node(d):
            default_value = self._get_default_value(d)
            if default_value is not None:
                res = default_value
                if self._is_multi_node(d) and not isinstance(res, list):
                    res = [res]
        elif self.is_tag(rpath):
            for k in list(conf):
                pos = self.relative_defaults(rpath + [k], conf[k])
                res |= pos
        else:
            for k in list(d):
                if k == 'node_data':
                    continue
                pos = self.relative_defaults(rpath + [k], conf.get(k, {}))
                res |= pos
        if res:
            if get_first_key or not rpath:
                if not isinstance(res, dict):
                    raise TypeError("Cannot get_first_key as data under node is not of type dict")
                return res
            return {rpath[-1]: res}

        return {}

    def merge_defaults(self, path: list, conf: dict) -> dict:
        if not path:
            path = [next(iter(conf.keys()))]
        if path[-1] in list(conf):
            config = conf[path[-1]]
            if not isinstance(config, dict):
                raise ValueError('conf at path is not of type dict')
            first = False
        else:
            config = conf
            first = True

        d = self.relative_defaults(path, conf=config, get_first_key=first)
        d = dict_merge(d, conf)
        return d
