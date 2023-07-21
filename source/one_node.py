from __future__ import annotations
import math
import random
import numpy as np
from lxml.etree import _Element
from rule_node import RuleNode
from field import Field
from observation import Observation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid
    from rule import Rule


class OneNode(RuleNode):

    def __init__(self) -> None:
        super().__init__()

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        if not super().load(element, parent_symmetry, grid):
            return False
        self.matches = []
        self.match_mask = np.full(
            (len(self.rules), len(self.grid.state)), False)
        return True

    def reset(self):
        super().reset()
        if self.match_count != 0:
            self.match_mask.fill(False)
            self.match_count = 0

    def apply(self, rule: Rule, x, y, z):
        """在网格中的位置(x, y, z)处应用规则，该位置必须使得整个输出模式都在边界内。"""
        mx, my = self.grid.mx, self.grid.my
        changes = self.ip.changes
        for dz in range(rule.omz):
            for dy in range(rule.omy):
                for dx in range(rule.omx):
                    new_value = rule.output[dx + dy *
                                            rule.omx + dz * rule.omx * rule.omy]
                    if new_value != 255:
                        sx = x + dx
                        sy = y + dy
                        sz = z + dz
                        si = sx + sy * mx + sz * mx * my
                        old_value = self.grid.state[si]
                        if new_value != old_value:
                            self.grid.state[si] = new_value
                            changes.append((sx, sy, sz))

    def go(self) -> bool:
        print("OneNode go")
        if not super().go():
            return False
        self.last_matched_turn = self.ip.counter
        if self.trajectory is not None:
            if self.counter >= len(self.trajectory):
                return False
            self.grid.state = self.trajectory[self.counter][:len(
                self.grid.state)]
            self.counter += 1
            return True
        r, x, y, z = self.random_match()
        if r < 0:
            return False
        else:
            self.last[r] = True
            self.apply(self.rules[r], x, y, z)
            self.counter += 1
            return True

    def random_match(self):
        if self.potentials is not None:
            if self.observations is not None and Observation.is_goal_reached(self.grid.state, self.future):
                self.future_computed = False
                return (-1, -1, -1, -1)
            max = -1000.0
            argmax = -1
            first_heuristic = 0.0
            first_heuristic_computed = False
            k = 0
            while k < self.match_count:
                r, x, y, z = self.matches[k]
                i = x + y * self.grid.mx + z * self.grid.mx * self.grid.my
                if not self.grid.matches(self.rules[r], x, y, z):
                    self.match_mask[r, i] = False
                    self.matches[k] = self.matches[self.match_count - 1]
                    self.match_count -= 1
                    k -= 1
                else:
                    heuristic = Field.delta_pointwise(
                        self.grid.state, self.rules[r], x, y, z, self.fields, self.potentials, self.grid.mx, self.grid.my)
                    if heuristic is None:
                        continue
                    if not first_heuristic_computed:
                        first_heuristic = heuristic
                        first_heuristic_computed = True
                    u = random.random()
                key = u ** math.exp((heuristic - first_heuristic) /
                                    self.temperature) if self.temperature > 0 else 0.001 * u - heuristic
                if key > max:
                    max = key
                    argmax = k
                k += 1
            return self.matches[argmax] if argmax >= 0 else (-1, -1, -1, -1)
        else:
            while self.match_count > 0:
                match_index = random.randint(0, self.match_count)
                r, x, y, z = self.matches[match_index]
                i = x + y * self.grid.mx + z * self.grid.mx * self.grid.my
                self.match_mask[r, i] = False
                self.matches[match_index] = self.matches[self.match_count - 1]
                self.match_count -= 1
                if self.grid.matches(self.rules[r], x, y, z):
                    return (r, x, y, z)
            return (-1, -1, -1, -1)


if __name__ == "__main__":
    random.seed(2)
    print(random.random())
    print(random.random())
    random.seed(2)
    print(random.randint(0, 99999))
    print(random.randint(0, 99999))
