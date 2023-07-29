from __future__ import annotations
import time
import numpy as np
from random import Random
from grid import Grid
from wfc_node import WFCNode
from helper import Helper
from graphic import Graphic
from symmetry_helper import SymmetryHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element


class OverlapNode(WFCNode):

    def __init__(self) -> None:
        super().__init__()

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        print("OverlapNode load")
        if grid.mz != 1:
            print("overlapping model currently works only for 2d")
            return False
        self.N = int(element.get("n", 3))
        symmetry_str = element.get("symmetry")
        symmetry = SymmetryHelper.get_symmetry(
            True, symmetry_str, parent_symmetry)
        if symmetry is None:
            print(
                f"unknown symmetry {symmetry_str} at line {element.sourceline}")
            return False
        periodic_input = bool(element.get("periodicInput", True))
        self.new_grid = Grid(element, grid.mx, grid.my, grid.mz)
        if self.new_grid is None:
            return False
        self.periodic = True
        self.name = element.get("sample")
        bitmap, smx, smy, _ = Graphic.load_bitmap(
            f"resources/samples/{self.name}.png")
        if bitmap is None:
            print(f"couldn't read sample {self.name}")
            return False
        sample, C = Helper.ords(bitmap)
        if C > self.new_grid.c:
            print(
                f"there were more than {self.new_grid.c} colors in the sample")
            return False
        W = C ** (self.N ** 2)

        def pattern_from_index(ind):
            residue = ind
            power = W
            result = []
            for i in range(self.N ** 2):
                power //= C
                count = 0
                while residue >= power:
                    residue -= power
                    count += 1
                result.append(count)
            return result

        weights = {}
        ordering = []
        ymax = grid.my if periodic_input else grid.my - self.N + 1
        xmax = grid.mx if periodic_input else grid.mx - self.N + 1
        for y in range(ymax):
            for x in range(xmax):
                pattern = Helper.pattern(lambda dx, dy: sample[(
                    x + dx) % smx + ((y + dy) % smy) * smx], self.N)
                symmetries = SymmetryHelper.square_symmetries(pattern, lambda q: Helper.rotated(
                    q, self.N), lambda q: Helper.reflected(q, self.N), lambda q1, q2: False, symmetry)
                for p in symmetries:
                    ind = Helper.index(p, C)
                    if ind in weights:
                        weights[ind] += 1
                    else:
                        weights[ind] = 1
                        ordering.append(ind)
        self.P = len(weights)
        print(f"number of patterns P = {self.P}")
        self.patterns = [0] * self.P
        self.weights = [0.0] * self.P
        counter = 0
        for w in ordering:
            self.patterns[counter] = pattern_from_index(w)
            self.weights[counter] = weights[w]
            counter += 1
        self.propagator = [None] * 4
        for d in range(4):
            self.propagator[d] = [None] * self.P
            for t in range(self.P):
                array = []
                for t2 in range(self.P):
                    if self.agrees(self.patterns[t], self.patterns[t2], self.DX[d], self.DY[d]):
                        array.append(t2)
                self.propagator[d][t] = [0] * len(array)
                for c, data in enumerate(array):
                    self.propagator[d][t][c] = data
        for rule_element in element.findall("rule"):
            input = rule_element.get("in")
            outputs = [self.new_grid.values[s[0]]
                       for s in rule_element.get("out").split("|")]
            position = [self.patterns[t][0]
                        in outputs for t in range(0, self.P)]
            self.map[grid.values[input]] = position
        if 0 not in self.map:
            self.map[0] = [True] * self.P
        return super().load(element, parent_symmetry, grid)

    def update_state(self):
        # TODO 执行太慢了
        start = time.time()
        mx, my = self.new_grid.mx, self.new_grid.my
        votes = np.full((len(self.new_grid.state), self.new_grid.c), 0)
        for i, w in enumerate(self.wave.data):
            x = i % mx
            y = i // mx
            for p in range(self.P):
                if w[p]:
                    pattern = self.patterns[p]
                    for dy in range(self.N):
                        ydy = y + dy
                        if ydy >= my:
                            ydy -= my
                        for dx in range(self.N):
                            xdx = x + dx
                            if xdx >= mx:
                                xdx -= mx
                            value = pattern[dx + dy * self.N]
                            votes[xdx + ydy * mx, value] += 1
        print(f"self.wave.data loop = {time.time() - start} s")
        r = Random()
        for i, v in enumerate(votes):
            max = -1.0
            argmax = 255
            for c, vc in enumerate(v):
                value = vc + 0.1 * r.random()
                if value > max:
                    argmax = c
                    max = value
            self.new_grid.state[i] = argmax

    def agrees(self, p1, p2, dx, dy):
        xmin = 0 if dx < 0 else dx
        xmax = dx + self.N if dx < 0 else self.N
        ymin = 0 if dy < 0 else dy
        ymax = dy + self.N if dy < 0 else self.N
        for y in range(ymin, ymax):
            for x in range(xmin, xmax):
                if p1[x + y * self.N] != p2[x - dx + (y - dy) * self.N]:
                    return False
        return True


if __name__ == "__main__":
    import sys
    print(sys.version)
