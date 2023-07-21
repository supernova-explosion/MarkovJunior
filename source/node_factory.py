from __future__ import annotations
from lxml.etree import QName
from lxml.etree import _Element
from one_node import OneNode
from map_node import MapNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from node import Node


class NodeFactory:

    node_map = {
        "one": OneNode,
        "all": OneNode,
        "prl": OneNode,
        "markov": OneNode,
        "sequence": MapNode,
        "path": OneNode,
        "map": MapNode,
        "convolution": OneNode,
        "convchain": OneNode,
        "wfc": OneNode
    }

    @staticmethod
    def factory(element: _Element, symmetry, ip, grid) -> Node:
        localname = QName(element).localname
        if localname not in NodeFactory.node_map:
            raise Exception(
                f"unknown node type \"{element.tag}\" at line {element.sourceline}")
        result: Node = NodeFactory.node_map[localname]()
        result.ip = ip
        result.grid = grid
        success = result.load(element, symmetry, grid)
        if not success:
            raise Exception(f"failed to load node \"{localname}\"")
        return result
