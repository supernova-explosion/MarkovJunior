from __future__ import annotations
from lxml.etree import QName
from one_node import OneNode
from all_node import AllNode
from map_node import MapNode
from path_node import PathNode
from parallel_node import ParallelNode
from conv_chain_node import ConvChainNode
from convolution_node import ConvolutionNode
from overlap_node import OverlapNode
from tile_node import TileNode
from branch import MarkovNode
from branch import SequenceNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from node import Node
    from interpreter import Interpreter
    from lxml.etree import _Element


class NodeFactory:

    @staticmethod
    def factory(element: _Element, symmetry, ip: Interpreter, grid) -> Node:
        node_map = {
            "one": OneNode,
            "all": AllNode,
            "prl": ParallelNode,
            "markov": MarkovNode,
            "sequence": SequenceNode,
            "path": PathNode,
            "map": MapNode,
            "convolution": ConvolutionNode,
            "convchain": ConvChainNode,
            "wfc": OverlapNode if element.get("sample") is not None else TileNode
        }
        localname = QName(element).localname
        if localname not in node_map:
            raise Exception(
                f"unknown node type \"{element.tag}\" at line {element.sourceline}")
        result: Node = node_map[localname]()
        result.ip = ip
        result.grid = grid
        success = result.load(element, symmetry, grid)
        if not success:
            raise Exception(f"failed to load node \"{localname}\"")
        return result


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    # 创建一个包含 5 个子图的图表
    fig, axes = plt.subplots(nrows=1, ncols=5, figsize=(15, 3))

    # 循环添加图像到每个子图
    for i in range(5):
        # 生成随机图像数据（这里简化为随机数）
        data = np.random.rand(10, 10)

        # 在第 i 个子图中展示图像
        axes[i].imshow(data, cmap='viridis', interpolation='nearest')
        axes[i].set_title(f'Subplot {i + 1}')

    # 调整子图之间的间距
    plt.tight_layout()

    # 显示所有子图
    plt.show()
