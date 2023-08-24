from __future__ import annotations
import math
import random
from field import Field
from rule_node import RuleNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid
    from lxml.etree import _Element


class AllNode(RuleNode):

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        if not super().load(element, parent_symmetry, grid):
            return False
        self.matches = []
        return True

    def fit(self, r, x, y, z, new_state: list[bool], mx, my):
        rule = self.rules[r]
        for dz in range(rule.omz):
            for dy in range(rule.omy):
                for dx in range(rule.omx):
                    value = rule.output[dx + dy *
                                        rule.omx + dz * rule.omx * rule.omy]
                    if value != 255 and new_state[x + dx + (y + dy) * mx + (z + dz) * mx * my]:
                        return
        self.last[r] = True
        for dz in range(rule.omz):
            for dy in range(rule.omy):
                for dx in range(rule.omx):
                    new_value = rule.output[dx + dy *
                                            rule.omx + dz * rule.omx * rule.omy]
                    if new_value != 255:
                        sx, sy, sz = x + dx, y + dy, z + dz
                        i = sx + sy * mx + sz * mx * my
                        new_state[i] = True
                        self.grid.state[i] = new_value
                        self.ip.changes.append((sx, sy, sz))

    def go(self) -> bool:
        # print("AllNode go")
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
        if self.match_count == 0:
            return False
        mx, my = self.grid.mx, self.grid.my
        if self.potentials is not None:
            first_heuristic = 0
            first_heuristic_computed = False
            data_list = []
            for m in range(self.match_count):
                r, x, y, z = self.matches[m]
                heuristic = Field.delta_pointwise(
                    self.grid.state, self.rules[r], x, y, z, self.fields, self.potentials, self.grid.mx, self.grid.my)
                if heuristic is not None:
                    if not first_heuristic_computed:
                        first_heuristic = heuristic
                        first_heuristic_computed = True
                    u = self.ip.random.random()
                    data_list.append((m, u ** math.exp((heuristic - first_heuristic) //
                                                       self.temperature) if self.temperature > 0 else 0.001 * u - heuristic))
            ordered = sorted(data_list, key=lambda x: -x[1])
            for item, _ in ordered:
                r, x, y, z = self.matches[item]
                self.match_mask[r, x + y * mx + z * mx * my] = False
                self.fit(r, x, y, z, self.grid.mask, mx, my)
        else:
            shuffle = list(range(self.match_count))
            self.ip.random.shuffle(shuffle)
            for i in shuffle:
                r, x, y, z = self.matches[i]
                self.match_mask[r, x + y * mx + z * mx * my] = False
                self.fit(r, x, y, z, self.grid.mask, mx, my)
        for n in range(self.ip.first[self.last_matched_turn], len(self.ip.changes)):
            x, y, z = self.ip.changes[n]
            self.grid.mask[x + y * mx + z * mx * my] = False
        self.counter += 1
        self.match_count = 0
        return True


if __name__ == "__main__":
    a = list(range(5))
    random.seed(1)
    random.shuffle(a)
    random.randint(1, 3)
    b = random.random()
    print(a, b)
