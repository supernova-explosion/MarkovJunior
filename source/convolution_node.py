from __future__ import annotations
import numpy as np
from node import Node
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from grid import Grid


class ConvolutionNode(Node):
    """
    ConvolutionNode根据节点的卷积规则，根据相邻网格单元的颜色来变换网格单元。
    当执行ConvolutionNode时，会在每个网格单元（如果有）上应用第一个匹配的卷积规则。
    """

    def __init__(self) -> None:
        self.counter = 0
        self.rules: list[ConvolutionRule] = []
        self.kernels2d = {
            "VonNeumann": [0, 1, 0, 1, 0, 1, 0, 1, 0],
            "Moore": [1, 1, 1, 1, 0, 1, 1, 1, 1]
        }
        self.kernels3d = {
            "VonNeumann": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "NoCorners": [0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0]
        }

    def load(self, element: _Element, symmetry: list[bool], grid: Grid) -> bool:
        rule_elements = element.findall("rule")
        if len(rule_elements) == 0:
            rule_elements = [element]
        self.rules = [None] * len(rule_elements)
        for k in range(len(self.rules)):
            self.rules[k] = ConvolutionRule()
            if not self.rules[k].load(rule_elements[k], grid):
                return False
        self.steps = int(element.get("steps", -1))
        self.periodic = bool(element.get("periodic", False))
        neighborhood = element.get("neighborhood")
        self.kernel = self.kernels2d[neighborhood] if grid.mz == 1 else self.kernels3d[neighborhood]
        self.sumfield = np.full((len(grid.state), grid.c), 0)
        return True

    def reset(self):
        self.counter = 0

    def go(self) -> bool:
        if self.steps > 0 and self.counter >= self.steps:
            return False
        self.sumfield.fill(0)
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        if mz == 1:
            for y in range(my):
                for x in range(mx):
                    sums = self.sumfield[x + y * mx]
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            sx = x + dx
                            sy = y + dy
                            if self.periodic:
                                if sx < 0:
                                    sx += mx
                                elif sx >= mx:
                                    sx -= mx
                                if sy < 0:
                                    sy += my
                                elif sy >= my:
                                    sy -= my
                            elif sx < 0 or sy < 0 or sx >= mx or sy >= my:
                                continue
                            sums[self.grid.state[sx + sy * mx]
                                 ] += self.kernel[dx + 1 + (dy + 1) * 3]
        else:
            for z in range(mz):
                for y in range(my):
                    for x in range(mx):
                        sums = self.sumfield[x + y * mx + z * mx * my]
                        for dz in range(-1, 2):
                            for dy in range(-1, 2):
                                for dx in range(-1, 2):
                                    sx = x + dx
                                    sy = y + dy
                                    sz = z + dz
                                    if self.periodic:
                                        if sx < 0:
                                            sx += mx
                                        elif sx >= mx:
                                            sx -= mx
                                        if sy < 0:
                                            sy += my
                                        elif sy > my:
                                            sy -= my
                                        if sz < 0:
                                            sz += mz
                                        elif sz >= mz:
                                            sz -= mz
                                    elif sx < 0 or sy < 0 or sz < 0 or sx >= mx or sy >= my or sz >= mz:
                                        continue
                                    sums[self.grid.state[sx + sy * mx + sz * mx * my]
                                         ] += self.kernel[dx + 1 + (dy + 1) * 3 + (dz + 1) * 9]
        change = False
        for i, sums in enumerate(self.sumfield):
            input = self.grid.state[i]
            for rule in self.rules:
                if input == rule.input and rule.output != self.grid.state[i] and (rule.p == 1.0 or self.ip.random.randint(0, 2 ** 32 - 1) < rule.p * 2 ** 32 - 1):
                    success = True
                    if rule.sums is not None:
                        sum = 0
                        for v in rule.values:
                            sum += sums[v]
                        success = rule.sums[sum]
                    if success:
                        self.grid.state[i] = rule.output
                        change = True
                        break
        self.counter += 1
        return change


class ConvolutionRule:

    def __init__(self) -> None:
        pass

    def load(self, element: _Element, grid: Grid):
        self.input = grid.values[element.get("in")]
        self.output = grid.values[element.get("out")]
        self.p = float(element.get("p", 1.0))
        value_str = element.get("values")
        sum_str = element.get("sum")
        if value_str is not None and sum_str is None:
            print(f"missing \"sum\" attribute at line {element.sourceline}")
            return False
        if value_str is None and sum_str is not None:
            print(f"missing \"values\" attribute at line {element.sourceline}")
            return False
        if value_str is not None:
            self.values = [grid.values[c] for c in value_str]
            self.sums = [False] * 28
            intervals = sum_str.split(",")
            for s in intervals:
                for i in __class__.interval(s):
                    self.sums[i] = True
        return True

    @staticmethod
    def interval(s):
        if "." in s:
            bounds = s.split("..")
            min = int(bounds[0])
            max = int(bounds[1])
            return [min + i for i in range(max - min + 1)]
        else:
            return [int(s)]


if __name__ == "__main__":
    a = np.full((2, 2), 0)
    np.ndenumerate
