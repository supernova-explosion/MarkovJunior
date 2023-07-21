from __future__ import annotations
from lxml.etree import _Element
from grid import Grid
from symmetry_helper import SymmetryHelper
from node import Node
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from map_node import MapNode
    from wfc_node import WFCNode
    from interpreter import Interpreter


class Branch(Node):

    parent: Branch = None

    nodes: list[Node] = []

    n = 0

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        # 避免循环导入，暂时没找到更好的方式
        from node_factory import NodeFactory
        print("Branch")
        symmetry_str = element.get("symmetry")
        symmetry = SymmetryHelper.get_symmetry(
            self.ip.grid.mz == 1, symmetry_str, parent_symmetry)
        if symmetry is None:
            print(f"unknown symmetry \"{symmetry_str}\"")
            return False
        path = ".//" + " or .//".join(self.node_names.keys())
        childrens = element.xpath(path)
        for children in childrens:
            child = NodeFactory.factory(children, symmetry, self.ip, grid)
            # child = super(Brunch, Brunch).factory(
            #     children, symmetry, self.ip, grid)
            if isinstance(child, Branch):
                child.parent = None if isinstance(
                    child, (MapNode, WFCNode)) else self
            self.nodes.append(child)
        return True

    def go(self) -> bool:
        print("Branch go")
        for node in self.nodes:
            if isinstance(node, Branch):
                self.ip.current = node
            if node.go():
                return True
        self.ip.current = self.ip.current.parent
        self.reset()
        return False

    def reset(self):
        self.n = 0
        for node in self.nodes:
            node.reset()


class SequenceNode(Branch):
    pass


class MarkovNode(Branch):

    def __init__(self) -> None:
        pass

    @classmethod
    def get_instance(cls, child: Node, ip: Interpreter) -> MarkovNode:
        node = cls()
        node.nodes = [child]
        node.ip = ip
        node.grid = ip.grid
        return node

    def go(self) -> bool:
        print("MarkovNode go")
        self.n = 0
        return super().go()


if __name__ == "__main__":
    print()
