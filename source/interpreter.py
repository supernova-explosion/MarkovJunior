import numpy as np
from lxml import etree
from lxml.etree import _Element
from grid import Grid
from symmetry_helper import SymmetryHelper
from node_factory import NodeFactory
from branch import Branch
from branch import MarkovNode


class Interpreter:

    def __init__(self, file_name, mx, my, mz) -> None:
        self.mx = mx
        self.my = my
        self.mz = mz
        self.gif = False
        self.counter = 0
        self.root = None
        self.current = None
        self.changes = []
        self.first = []
        self.origin = None
        self.start_grid = None
        self.grid = None
        self.load(file_name, mx, my, mz)

    def load(self, file_name, mx, my, mz):
        element: _Element = etree.parse(file_name).getroot()
        self.origin = element.get("origin", False)
        self.start_grid = Grid(element, mx, my, mz)
        symmetry_str = element.get("symmetry")
        is_2d = self.start_grid.mz == 1
        symmetry = SymmetryHelper.get_symmetry(
            is_2d, symmetry_str, np.ones(8 if is_2d else 48, dtype=bool))
        if symmetry is None:
            raise Exception(
                f"unknown symmetry \"{symmetry_str}\" at line {element.sourceline}")
        top_node = NodeFactory.factory(
            element, symmetry, self, self.start_grid)
        # self.root = Brunch(top_node) if isinstance(
        #     top_node, Brunch) else MarkovNode.get_instance(top_node, self)
        self.root = top_node if isinstance(
            top_node, Branch) else MarkovNode.get_instance(top_node, self)

    def run(self, steps, gif):
        self.grid = self.start_grid
        self.grid.clear()
        if self.origin:
            self.grid.state[self.grid.mx // 2 + (self.grid.my // 2) * self.grid.mx + (
                self.grid.mz // 2) * self.grid.mx * self.grid.my] = 1
        self.changes.clear()
        self.first.clear()
        self.first.append(0)
        self.root.reset()
        self.current = self.root
        self.gif = gif
        self.counter = 0
        while self.current is not None and (steps <= 0 or self.counter < steps):
            if gif:
                print(f"[{self.counter}]")
                yield self.grid.state, self.grid.characters, self.grid.mx, self.grid.my, self.grid.mz
            self.current.go()
            self.counter += 1
            self.first.append(len(self.changes))
        yield self.grid.state, self.grid.characters, self.grid.mx, self.grid.my, self.grid.mz


if __name__ == "__main__":
    # ip = Interpreter("models/BacktrackerCycle.xml", 1, 1, 1)
    colors = etree.parse(
        f"resources/palette.xml").getroot().findall("color")
    for color in colors:
        print(color.sourceline)