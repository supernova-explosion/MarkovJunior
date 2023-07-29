from __future__ import annotations
from numpy import ndarray
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from rule import Rule
    from grid import Grid


class Field:

    def __init__(self, element: _Element, grid: Grid) -> None:

        self.inversed = False
        """如果为True，则计算grid state的分数时，distance字段的符号将被反转"""

        self.recompute = bool(element.get("recompute", False))
        self.essential = bool(element.get("essential", False))
        on = element.get("on")

        self.substrate = grid.wave(on)
        """势场的底色bitmask"""

        zero_symbols = element.get("from")
        if zero_symbols is not None:
            self.inversed = True
        else:
            zero_symbols = element.get("to")

        self.zero = grid.wave(zero_symbols)
        """势场中零点的颜色bitmask，potentials是经过substrate单元格到zero的最短路径"""

    def compute(self, potential: ndarray, grid: Grid):
        mx, my, mz = grid.mx, grid.my, grid.mz
        front = []
        ix = iy = iz = 0
        for i, value in enumerate(grid.state):
            potential[i] = -1
            if (self.zero & 1 << value) != 0:
                potential[i] = 0
                front.append((0, ix, iy, iz))
            ix += 1
            if ix == mx:
                ix = 0
                iy += 1
                if iy == my:
                    iy = 0
                    iz += 1
        if not front:
            return False
        while front:
            t, x, y, z = front.pop(0)
            neighbors = __class__.neighbors(x, y, z, mx, my, mz)
            for nx, ny, nz in neighbors:
                i = nx + ny * mx + nz * mx * my
                v = grid.state[i]
                if potential[i] == -1 and (self.substrate & 1 << v) != 0:
                    front.append((t + 1, nx, ny, nz))
                    potential[i] = t + 1
        return True

    @staticmethod
    def neighbors(x, y, z, mx, my, mz):
        result = []
        if x > 0:
            result.append((x - 1, y, z))
        if x < mx - 1:
            result.append((x + 1, y, z))
        if y > 0:
            result.append((x, y - 1, z))
        if y < my - 1:
            result.append(((x, y + 1, z)))
        if z > 0:
            result.append((x, y, z - 1))
        if z < mz - 1:
            result.append((x, y, z + 1))
        return result

    @staticmethod
    def delta_pointwise(state: list[int], rule: Rule, x, y, z, fields: list[Field], potentials: ndarray, mx, my):
        sum = 0
        dx = dy = dz = 0
        for input_value, new_value in zip(rule.input, rule.output):
            if new_value != 255 and (input_value & 1 << new_value) == 0:
                i = x + dx + (y + dy) * mx + (z + dz) * mx * my
                new_potential = potentials[new_value, i]
                if new_potential == -1:
                    return None
                old_value = state[i]
                old_potential = potentials[old_value, i]
                sum += new_potential - old_potential
                if fields is not None:
                    old_field = fields[old_value]
                    if old_field is not None and old_field.inversed:
                        sum += 2 * old_potential
                    new_field = fields[new_value]
                    if new_field is not None and new_field.inversed:
                        sum -= 2 * new_potential
            dx += 1
            if dx == rule.imx:
                dx = 0
                dy += 1
                if dy == rule.imy:
                    dy = 0
                    dz += 1
        return sum


if __name__ == "__main__":
    a = 3 << 2 & 0
    b = (3 << 2) & 0
    print(a, b)
