from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid
    from rule import Rule
    from numpy import ndarray


class Observation:

    def __init__(self, fro, to, grid: Grid) -> None:
        self.fro = grid.values[fro]
        """from颜色对应的索引"""

        self.to = grid.wave(to)
        """to颜色对应的bitmask"""

    @staticmethod
    def compute_future_set_present(future: list[int], state: list[int], observations: list[Observation]):
        """
        根据当前状态和适用于每种颜色的观察结果计算未来状态，同时将每个观察到的颜色替换为观察的from颜色。
        如果所有观察的颜色都存在于grid中，则返回True。
        """
        mask = [False] * len(observations)
        # 没被观察或存在于grid中的颜色都会被标记为True
        for i, observation in enumerate(observations):
            if observation is None:
                mask[i] = True
        # value对应颜色索引
        for i, value in enumerate(state):
            obs = observations[value]
            mask[value] = True
            if obs is not None:
                future[i] = obs.to
                state[i] = obs.fro
            else:
                future[i] = 1 << value
        # 返回False，说明存在被观察，但grid中却不包含的颜色
        for m in mask:
            if not m:
                return False
        return True

    @staticmethod
    def compute_forward_potentials(potentials: ndarray, state: list[int], mx, my, mz, rules: list[Rule]):
        """
        计算给定grid state的正向势。正向势potentials[c][x + y * mx + z * mx * my]，
        表示遵循rules到达颜色c所在位置(x, y, z)的状态所需重写次数的最小值。势为-1表示无法到达该状态。
        """
        potentials.fill(-1)
        for i, v in enumerate(state):
            potentials[v, i] = 0
        Observation.compute_potentials(potentials, mx, my, mz, rules, False)

    @staticmethod
    def compute_backward_potentials(potentials: ndarray, future: list[int], mx, my, mz, rules: list[Rule]):
        for c in range(potentials.shape[0]):
            potential = potentials[c]
            for i, f in enumerate(future):
                potential[i] = 0 if (f & (1 << c)) != 0 else -1
        Observation.compute_potentials(potentials, mx, my, mz, rules, True)

    @staticmethod
    def compute_potentials(potentials: ndarray, mx, my, mz, rules: list[Rule], backwards=False):
        queue = []
        for (c, i), element in np.ndenumerate(potentials):
            if element == 0:
                queue.append(
                    (c, i % mx, (i % (mx * my)) // mx, i // (mx * my)))
        match_mask = np.full((len(rules), len(potentials[0])), False)
        while queue:
            value, x, y, z = queue.pop(0)
            i = x + y * mx + z * mx * my
            t = potentials[value, i]
            for r, rule in enumerate(rules):
                maskr = match_mask[r]
                shifts = rule.oshifts[value] if backwards else rule.ishifts[value]
                for shiftx, shifty, shiftz in shifts:
                    sx = x - shiftx
                    sy = y - shifty
                    sz = z - shiftz
                    if sx < 0 or sy < 0 or sz < 0 or (sx + rule.imx) > mx or (sy + rule.imy) > my or (sz + rule.imz) > mz:
                        continue
                    si = sx + sy * mx + sz * mx * my
                    if not maskr[si] and Observation.forward_matches(rule, sx, sy, sz, potentials, t, mx, my, backwards):
                        maskr[si] = True
                        Observation.apply_forward(
                            rule, sx, sy, sz, potentials, t, mx, my, backwards, queue)

    @staticmethod
    def forward_matches(rule: Rule, x, y, z, potentials: ndarray, t, mx, my, backwards):
        dx = dy = dz = 0
        a = rule.output if backwards else rule.input
        for value in a:
            if value != 255:
                current = potentials[value, x + dx +
                                     (y + dy) * mx + (z + dz) * mx * my]
                if current > t or current == -1:
                    return False
            dx += 1
            if dx == rule.imx:
                dx = 0
                dy += 1
                if dy == rule.imy:
                    dy = 0
                    dz += 1
        return True

    @staticmethod
    def apply_forward(rule: Rule, x, y, z, potentials: ndarray, t, mx, my, backwards, q: list):
        a = rule.binput if backwards else rule.output
        for dz in range(rule.imz):
            zdz = z + dz
            for dy in range(rule.imy):
                ydy = y + dy
                for dx in range(rule.imx):
                    xdx = x + dx
                    idi = xdx + ydy * mx + zdz * mx * my
                    di = dx + dy * rule.imx + dz * rule.imx * rule.imy
                    o = a[di]
                    if o != 255 and potentials[o, idi] == -1:
                        potentials[o, idi] = t + 1
                        q.append((o, xdx, ydy, zdz))

    @staticmethod
    def is_goal_reached(present: list[int], future: list[int]):
        for p, f in zip(present, future):
            if ((1 << p) & f) == 0:
                return False
        return True

    @staticmethod
    def forward_pointwise(potentials: ndarray, future: list[int]):
        """使用给定的前向势计算与未来状态匹配的网格的最小分数，分数为-1表示无法到达目标"""
        sum = 0
        for i, f in enumerate(future):
            min = 1000
            argmin = -1
            for c in range(potentials.shape[0]):
                potential = potentials[c, i]
                if (f & 1) == 1 and potential >= 0 and potential < min:
                    min = potential
                    argmin = c
            if argmin < 0:
                return -1
            sum += min
        return sum

    @staticmethod
    def backward_pointwise(potentials: ndarray, present: list[int]):
        """使用给定的后向势计算网格的分数，分数为-1表示无法到达目标"""
        sum = 0
        for i, v in enumerate(present):
            potential = potentials[v, i]
            if potential < 0:
                return -1
            sum += potential
        return sum


if __name__ == "__main__":
    a = {tuple([1, 2]): 1}
    print(a)
