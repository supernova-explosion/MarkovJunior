from __future__ import annotations
from abc import abstractmethod
from lxml.etree import _Element
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid
    from interpreter import Interpreter


class Node:

    node_names = ["one", "all", "prl", "markov", "sequence",
                  "path", "map", "convolution", "convchain", "wfc"]

    ip: Interpreter = None

    grid: Grid = None

    @abstractmethod
    def load(element: _Element, symmetry: list[bool], grid: Grid) -> bool:
        pass

    @abstractmethod
    def reset():
        pass

    @abstractmethod
    def go() -> bool:
        pass


if __name__ == "__main__":
    pass
