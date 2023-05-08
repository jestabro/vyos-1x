
from typing import Union
from vyos.util import get_sub_dict

class Xml:
    def __init__(self):
        try:
            from xml_cache import definition
        except Exception:
            raise ImportError

        self.defs = definition

    def define(self, ref: dict):
        self.defs = ref

    def _get_ref_node_data(self, node: dict, data: str) -> Union[bool, str]:
        res = node.get('node_data', {})
        if not res:
            raise ValueError("non-existent node data")
        if data not in res:
            raise ValueError("non-existent data field")

        return res.get(data)

    def _get_ref_path(self, path: list) -> dict:
        ref_path = path.copy()
        d = self.defs
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
        d = self.defs
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
        return  self._get_ref_node_data(node, 'multi')

    def is_multi(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return  self._is_multi_node(d)

    def _is_valueless_node(self, node: dict) -> bool:
        return  self._get_ref_node_data(node, 'valueless')

    def is_valueless(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return  self._is_valueless_node(d)

    def _is_leaf_node(self, node: dict) -> bool:
        res = self._get_ref_node_data(node, 'node_type')
        return res == 'leaf'

    def is_leaf(self, path: list) -> bool:
        d = self._get_ref_path(path)
        return self._is_leaf_node(d)

    def multi_to_list(self, rpath: list, d: dict) -> dict:
        pass

    def _get_default_value(self, node: dict):
        return self._get_ref_node_data(node, "default_value")

    def get_defaults(self, path: list, get_first_key=False) -> dict:
        res = {}
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
            if get_first_key:
                if not isinstance(res, dict):
                    raise TypeError("Cannot get_first_key as data under node is not of type dict")
                return res
            return {path[-1]: res}

        return {}

    def relative_defaults(self, path: list, conf: dict = None, get_first_key=False) -> dict:
        if conf is None:
            conf = {}
        res = {}
        d = self._get_ref_path(path)
        if self._is_leaf_node(d):
            default_value = self._get_default_value(d)
            if default_value is not None:
                res = default_value
                if self._is_multi_node(d) and not isinstance(res, list):
                    res = [res]
        elif self.is_tag(path):
            for k in list(conf):
                pos = self.relative_defaults(path + [k], conf[k])
                res |= pos
        else:
            for k in list(d):
                if k == 'node_data':
                    continue
                pos = self.relative_defaults(path + [k], conf.get(k, {}))
                res |= pos
        if res:
            if get_first_key:
                if not isinstance(res, dict):
                    raise TypeError("Cannot get_first_key as data under node is not of type dict")
                return res
            return {path[-1]: res}

        return {}

    def merge_defaults(self, path: list, conf: dict) -> dict:
        if path[-1] in list(conf):
            conf = conf[path[-1]]
            if not isinstance(conf, dict):
                raise ValueError('conf at path is not of type dict')
            first = False
        else:
            first = True

        return self.relative_defaults(path, conf=conf, get_first_key=first)
