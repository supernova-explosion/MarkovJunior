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
    def load(self, element: _Element, symmetry: list[bool], grid: Grid) -> bool:
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def go(self) -> bool:
        pass


if __name__ == "__main__":
    import random

    random.seed(1)
    a = random.randint(0, 10000)
    b = random.random()
    print(a, b)
