from __future__ import annotations
import math
import random
from node import Node
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from grid import Grid
    from random import Random


class PathNode(Node):
    """
    PathNode节点在网格中的特定颜色之间绘制路径。在每个执行步骤中，都会选择一个start单元格，
    通过substrate单元格绘制一条到end单元格的最短路径。如果无法绘制这样的路径，则该节点不适用。
    """

    def __init__(self) -> None:
        pass

    def load(self, element: _Element, symmetry: list[bool], grid: Grid) -> bool:
        start_symbols = element.get("from")
        self.start = grid.wave(start_symbols)
        self.finish = grid.wave(element.get("to"))
        self.substrate = grid.wave(element.get("on"))

        self.value = grid.values[element.get("color", start_symbols[0])]
        """路径颜色"""

        self.inertia = bool(element.get("inertia", False))
        """如果为True，则查找路径时将保持惯性，即各个方向的成本相同时保持上一个选择的方向。如果为False，则随机选择。"""

        self.longest = bool(element.get("longest", False))
        """如果为True，则查找路径时将选择距结束位置最远的起始位置。如果为False，将选择距结束位置最近的起始位置。"""

        self.edges = bool(element.get("edges", False))
        """如果为True，路径可能包括二维的对角线steps。"""

        self.vertices = bool(element.get("vertices", False))
        """如果为True，路径可能包括三维的对角线steps。"""

        return True

    def go(self) -> bool:
        frontier = []
        start_positions = []
        generations = [-1] * len(self.grid.state)
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        for z in range(mz):
            for y in range(my):
                for x in range(mx):
                    i = x + y * mx + z * mx * my
                    # TODO 可以删除？
                    generations[i] = -1
                    s = self.grid.state[i]
                    # 不等于0说明颜色相同或者是通配符。&左右两个数字只有最高位是1，其他位是0，所以最高位相同时，&运算结果不等于0。
                    # 而两个数字都是通过1左移索引位得到的，最高位相同说明颜色索引一定相同或者是通配符。
                    # 因为通配符所有位都是1，另一个数字最高位是1，对应位也满足“都是1”这个条件
                    if (self.start & 1 << s) != 0:
                        start_positions.append((x, y, z))
                    if (self.finish & 1 << s) != 0:
                        generations[i] = 0
                        frontier.append((0, x, y, z))
        if not start_positions or not frontier:
            return False

        def push(t, x, y, z):
            i = x + y * mx + z * mx * my
            v = self.grid.state[i]
            if generations[i] == -1 and ((self.substrate & 1 << v) != 0 or (self.start & 1 << v) != 0):
                if (self.substrate & 1 << v) != 0:
                    frontier.append((t, x, y, z))
                generations[i] = t

        # 广度优先
        while frontier:
            t, x, y, z = frontier.pop(0)
            for dx, dy, dz in __class__.directions(x, y, z, mx, my, mz, self.edges, self.vertices):
                push(t + 1, x + dx, y + dy, z + dz)

        # 如果没有起始位置可以通过路径到达结束位置，则该节点不适用
        if not list(filter(lambda p: generations[p[0] + p[1] * mx + p[2] * mx * my] > 0, start_positions)):
            return False
        # 选择距结束位置最近（或最远）的开始位置
        local_random = random.Random(self.ip.random.random())
        min = mx * my * mz
        max = -2
        argmin = (-1, -1, -1)
        argmax = (-1, -1, -1)
        for px, py, pz in start_positions:
            g = generations[px + py * mx + pz * mx * my]
            if g == -1:
                continue
            dg = g
            noise = 0.1 * local_random.random()
            if dg + noise < min:
                min = dg + noise
                argmin = (px, py, pz)
            if dg + noise > max:
                max = dg + noise
                argmax = (px, py, pz)
        penx, peny, penz = argmax if self.longest else argmin
        # 开始绘制路径之前，先在路径中前进一步
        dirx, diry, dirz = self.direction(
            penx, peny, penz, 0, 0, 0, generations, local_random)
        penx += dirx
        peny += diry
        penz += dirz
        # 不等于0说明没有到达结束位置
        while generations[penx + peny * mx + penz * mx * my] != 0:
            self.grid.state[penx + peny * mx + penz * mx * my] = self.value
            self.ip.changes.append((penx, peny, penz))
            dirx, diry, dirz = self.direction(
                penx, peny, penz, dirx, diry, dirz, generations, local_random)
            penx += dirx
            peny += diry
            penz += dirz
        return True

    def direction(self, x, y, z, dx, dy, dz, generations: list[int], random: Random):
        candidates = []
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        g = generations[x + y * mx + z * mx * my]

        def add(addx, addy, addz):
            if generations[x + addx + (y + addy) * mx + (z + addz) * mx * my] == g - 1:
                candidates.append((addx, addy, addz))

        if not self.vertices and not self.edges:
            if self.inertia and (dx != 0 or dy != 0 or dz != 0):
                cx, cy, cz = x + dx, y + dy, z + dz
                if cx >= 0 and cy >= 0 and cz >= 0 and cx < mx and cy < my and cz < mz and generations[cx + cy * mx + cz * mx * my] == g - 1:
                    return dx, dy, dz
            if x > 0:
                add(-1, 0, 0)
            if x < mx - 1:
                add(1, 0, 0)
            if y > 0:
                add(0, -1, 0)
            if y < my - 1:
                add(0, 1, 0)
            if z > 0:
                add(0, 0, -1)
            if z < mz - 1:
                add(0, 0, 1)
            return random.choice(candidates)
        else:
            for px, py, pz in __class__.directions(x, y, z, mx, my, mz, self.edges, self.vertices):
                add((px, py, pz))
            result = (-1, -1, -1)
            if self.inertia and (dx != 0 or dy != 0 or dz != 0):
                max_scalar = -4
                for canx, cany, canz in candidates:
                    noise = 0.1 * random.random()
                    cos = (canx * dx + cany * dy + canz * dz) // math.sqrt((canx *
                                                                            canx + cany * cany + canz * canz) * (dx * dx + dy * dy + dz * dz))
                    if cos + noise > max_scalar:
                        max_scalar = cos + noise
                        result = (canx, cany, canz)
            else:
                result = random.choice(candidates)
            return result

    @staticmethod
    def directions(x, y, z, mx, my, mz, edges, vertices):
        result = []
        if mz == 1:
            if x > 0:
                result.append((-1, 0, 0))
            if x < mx - 1:
                result.append((1, 0, 0))
            if y > 0:
                result.append((0, -1, 0))
            if y < my - 1:
                result.append((0, 1, 0))
            if edges:
                if x > 0 and y > 0:
                    result.append((-1, -1, 0))
                if x > 0 and y < my - 1:
                    result.append((-1, 1, 0))
                if x < mx - 1 and y > 0:
                    result.append((1, -1, 0))
                if x < mx - 1 and y < my - 1:
                    result.append((1, 1, 0))
        else:
            if x > 0:
                result.append((-1, 0, 0))
            if x < mx - 1:
                result.append((1, 0, 0))
            if y > 0:
                result.append((0, -1, 0))
            if y < my - 1:
                result.append((0, 1, 0))
            if z > 0:
                result.append((0, 0, -1))
            if z < mz - 1:
                result.append((0, 0, 1))
            if edges:
                if x > 0 and y > 0:
                    result.append((-1, -1, 0))
                if x > 0 and y < my - 1:
                    result.append((-1, 1, 0))
                if x < mx - 1 and y > 0:
                    result.append((1, -1, 0))
                if x < mx - 1 and y < my - 1:
                    result.append((1, 1, 0))
                if x > 0 and z > 0:
                    result.append((-1, 0, -1))
                if x > 0 and z < mz - 1:
                    result.append((-1, 0, 1))
                if x < mx - 1 and z > 0:
                    result.append((1, 0, -1))
                if x < mx - 1 and z < mz - 1:
                    result.append((1, 0, 1))
                if y > 0 and z > 0:
                    result.append((0, -1, -1))
                if y > 0 and z < mz - 1:
                    result.append((0, -1, 1))
                if y < my - 1 and z > 0:
                    result.append((0, 1, -1))
                if y < my - 1 and z < mz - 1:
                    result.append((0, 1, 1))
            if vertices:
                if x > 0 and y > 0 and z > 0:
                    result.append((-1, -1, -1))
                if x > 0 and y > 0 and z < mz - 1:
                    result.append((-1, -1, 1))
                if x > 0 and y < my - 1 and z > 0:
                    result.append((-1, 1, -1))
                if x > 0 and y < my - 1 and z < mz - 1:
                    result.append((-1, 1, 1))
                if x < mx - 1 and y > 0 and z > 0:
                    result.append((1, -1, -1))
                if x < mx - 1 and y > 0 and z < mz - 1:
                    result.append((1, -1, 1))
                if x < mx - 1 and y < my - 1 and z > 0:
                    result.append((1, 1, -1))
                if x < mx - 1 and y < my - 1 and z < mz - 1:
                    result.append((1, 1, 1))
        return result


if __name__ == "__main__":
    import numpy as np
    a = np.reshape([10, 9, 8, 9, 9, 8, 7, 6, 7, 8, 9, 8, 7, 8, 10, 9, 6, 5, 6, 7, 8, 7, 6, 7, -1, -1, 5, 4, 5, 6, 7, 6, 5, 4, 3, 3, 3, 3, 4, 5, 6, 5, 4, 3, 2, 2, 2, 2, 3,
                   4, 5, 4, 3, 2, 1, 1, 1, 1, 2, 3, 4, 3, 2, 1, 0, 0, 0, 0, 1, 2, 4, 3, 2, 1, 0, 0, 0, 0, 1, 2, 4, 3, 2, 1, 0, 0, 0, 0, 1, 2, 5, 4, 3, 2, 1, 1, 1, 1, 2, 3], (10, 10))
    print(a)
