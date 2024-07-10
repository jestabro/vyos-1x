# Copyright 2024 VyOS maintainers and contributors <maintainers@vyos.io>
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

from graphlib import TopologicalSorter
from graphlib import CycleError
from typing import TypeVar

from vyos.utils.system import load_as_module


N = TypeVar('N')
GraphData = dict[N, set[N]] | list[tuple[N, N]]


class GraphCycleError(Exception):
    """Custom exception raised when a cycle is detected in the graph"""

    pass


class Graph:
    """Graph class to represent a directed graph"""

    def __init__(self, data: GraphData) -> None:
        """Graph class constructor

        Args:
            data (GraphData): Data to initialize the graph in one of two forms:
                - A dictionary with nodes as keys and a set of nodes as
                  values {target: {source1, source2, ...}}
                  This is the representation used by the graphlib library.
                - A list of tuples with each tuple containing two nodes
                  (source, target)
                  This representation make some operations more readable.
                Any update to one representation will update the other.

        Raises:
            GraphCycleError: If a cycle is detected in the initializtion
            data
        """
        self.__node_set: set[N] = set()
        self.__node_repr: dict[N, set[N]] = {}
        self.__edge_repr: list[tuple[N, N]] = []

        if isinstance(data, dict) and all(isinstance(v, set) for v in
                                          data.values()):
            self.__node_repr = data
            self.__edge_repr = self.__node_to_edge(data)
        elif isinstance(data, list) and all(isinstance(t, tuple) and
                                            len(t) == 2 for t in data):
            self.__edge_repr = data
            self.__node_repr = self.__edge_to_node(data)
        else:
            raise ValueError('Invalid graph data format')

    @staticmethod
    def __sort_node(nodes: dict[N, set[N]]) -> dict[N, set[N]]:
        return {k: set(sorted(v)) for k, v in nodes.items()}
        dict(sorted(self.component.items(), key=lambda x: x[0]))


    @staticmethod
    def __sort_edge(edges: list[tuple[N, N]]) -> list[tuple[N, N]]:
        return sorted(edges, key=lambda x: (str(x[0]), str(x[1])))

    @staticmethod
    def __node_to_edge(nodes: dict[N, set[N]]) -> list[tuple[N, N]]:
        """Convert node representation to edge representation

        Args:
            data (dict[N, set[N]]): Node representation

        Returns:
            list[tuple[N, N]]: Edge representation
        """
        edges = [(source, target) for target, sources in nodes.items()
                 for source in sources]

        return edges

    @staticmethod
    def __edge_to_node(edges: list[tuple[N, N]]) -> dict[N, set[N]]:
        """Convert edge representation to node representation

        Args:
            data (list[tuple[N, N]]): Edge representation

        Returns:
            dict[N, set[N]]: Node representation
        """
        nodes = {}
        for source, target in edges:
            if target not in nodes:
                nodes[target] = set()
            nodes[target].add(source)

        return nodes
