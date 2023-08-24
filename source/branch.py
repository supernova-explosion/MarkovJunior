from __future__ import annotations
import time
from lxml import etree
from grid import Grid
from symmetry_helper import SymmetryHelper
from node import Node
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from interpreter import Interpreter


class Branch(Node):

    def __init__(self) -> None:

        self.parent: Branch = None

        self.nodes: list[Node] = []

        self.n = 0
        """当前活动子节点的索引，如果需要进行任何预处理，则可能为-1"""

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        # 避免循环导入，暂时没找到更好的方式
        from map_node import MapNode
        from wfc_node import WFCNode
        from node_factory import NodeFactory

        # print("Branch load", element)
        symmetry_str = element.get("symmetry")
        symmetry = SymmetryHelper.get_symmetry(
            self.ip.grid.mz == 1, symmetry_str, parent_symmetry)
        if symmetry is None:
            print(f"unknown symmetry \"{symmetry_str}\"")
            return False
        path = " | ".join(self.node_names)
        childrens: list[_Element] = element.xpath(path)
        for children in childrens:
            child = NodeFactory.factory(children, symmetry, self.ip, grid)
            if isinstance(child, Branch):
                child.parent = None if isinstance(
                    child, (MapNode, WFCNode)) else self
            self.nodes.append(child)
        # print(f"Branch load time = {time.time() - start} s", element)
        return True

    def go(self) -> bool:
        # print("Branch go")
        # go返回True，则n不变，下次循环继续执行同一个node
        # go返回False，则n + 1，开始执行下一个节点
        while self.n < len(self.nodes):
            node = self.nodes[self.n]
            if isinstance(node, Branch):
                self.ip.current = node
            if node.go():
                return True
            self.n += 1
        self.ip.current = self.ip.current.parent
        self.reset()
        return False

    def reset(self):
        for node in self.nodes:
            node.reset()
        self.n = 0


class SequenceNode(Branch):
    """SequenceNode按顺序执行每个子节点，直到它们不适用为止。"""

    def __init__(self) -> None:
        super().__init__()


class MarkovNode(Branch):
    """MarkovNode每次都从第一个子节点开始执行，直到所有子节点均不适用。"""

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def get_instance(cls, child: Node, ip: Interpreter) -> MarkovNode:
        node = cls()
        node.nodes = [child]
        node.ip = ip
        node.grid = ip.grid
        return node

    def go(self) -> bool:
        # print("MarkovNode go")
        self.n = 0
        return super().go()


if __name__ == "__main__":
    xml_content = '''
    <root>
        <element1>Value 1</element1>
        <element2>Value 2</element2>
        <element3>
            <element1>Value 3-1</element1>
            <element2>Value 3-2</element2>
        </element3>
        <element4>Value 4</element4>
    </root>
    '''

    # 解析 XML 文档
    root = etree.fromstring(xml_content)

    # 获取标签为 <element1> 和 <element2> 的子节点列表
    # elements_1_and_2 = root.xpath(".//element1 | .//element2")
    elements_1_and_2 = root.xpath("element1 | element2")

    # 打印子节点的标签和文本内容
    for element in elements_1_and_2:
        print(element)
