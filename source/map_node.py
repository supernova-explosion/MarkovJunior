from __future__ import annotations
from branch import Branch
from grid import Grid
from rule import Rule
from symmetry_helper import SymmetryHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element


class MapNode(Branch):

    def __init__(self) -> None:
        super().__init__()
        self.new_grid: Grid = None
        self.rules: list[Rule] = []
        self.nx = 0
        self.dx = 0
        self.ny = 0
        self.dy = 0
        self.nz = 0
        self.dz = 0

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        scale_str = element.get("scale")
        if scale_str is None:
            print("scale should be specified in map node")
            return False
        scales = scale_str.split()
        if len(scales) != 3:
            print(
                f"scale attribute \"{scale_str}\" should have 3 components separated by space")
            return False
        self.nx, self.dx = __class__.read_scale(scales[0])
        self.ny, self.dy = __class__.read_scale(scales[1])
        self.nz, self.dz = __class__.read_scale(scales[2])
        self.new_grid = Grid(element, grid.mx * self.nx // self.dx,
                             grid.my * self.ny // self.dy, grid.mz * self.nz // self.dz)
        if self.new_grid is None:
            return False
        if not super().load(element, parent_symmetry, self.new_grid):
            return False
        is_2d = grid.mz == 1
        symmetry = SymmetryHelper.get_symmetry(
            is_2d, element.get("symmetry"), parent_symmetry)
        for rule_element in element.findall("rule"):
            rule = Rule.load(rule_element, grid, self.new_grid)
            if rule is None:
                return False
            rule.original = True
            for r in rule.symmetries(symmetry, is_2d):
                self.rules.append(r)
        return True

    def go(self) -> bool:
        if self.n >= 0:
            return super().go()
        self.new_grid.clear()
        for rule in self.rules:
            for z in range(self.grid.mz):
                for y in range(self.grid.my):
                    for x in range(self.grid.mx):
                        if __class__.matches(rule, x, y, z, self.grid.state, self.grid.mx, self.grid.my, self.grid.mz):
                            __class__.apply(rule, x * self.nx // self.dx, y * self.ny // self.dy, z *
                                            self.nz // self.dz, self.new_grid.state, self.new_grid.mx, self.new_grid.my, self.new_grid.mz)
        self.ip.grid = self.new_grid
        self.n += 1
        return True

    def reset(self):
        super().reset()
        self.n -= 1

    @staticmethod
    def read_scale(s):
        if "/" not in s:
            return int(s), 1
        else:
            nd = s.split("/")
            return int(nd[0]), int(nd[1])

    @staticmethod
    def matches(rule: Rule, x, y, z, state: list[bool], mx, my, mz):
        for dz in range(rule.imz):
            for dy in range(rule.imy):
                for dx in range(rule.imx):
                    sx = x + dx
                    sy = y + dy
                    sz = z + dz
                    if sx >= mx:
                        sx -= mx
                    if sy >= my:
                        sy -= my
                    if sz >= mz:
                        sz -= mz
                    input_wave = rule.input[dx + dy *
                                            rule.imx + dz * rule.imx * rule.imy]
                    if (input_wave & (1 << state[sx + sy * mx + sz * mx * my])) == 0:
                        return False
        return True

    @staticmethod
    def apply(rule: Rule, x, y, z, state: list[bool], mx, my, mz):
        for dz in range(rule.omz):
            for dy in range(rule.omy):
                for dx in range(rule.omx):
                    sx = x + dx
                    sy = y + dy
                    sz = z + dz
                    if sx >= mx:
                        sx -= mx
                    if sy >= my:
                        sy -= my
                    if sz >= mz:
                        sz -= mz
                    output = rule.output[dx + dy *
                                         rule.omx + dz * rule.omx * rule.omy]
                    if output != 255:
                        state[sx + sy * mx + sz * mx * my] = output


if __name__ == "__main__":
    s = "abc"
    print("a" in s)
