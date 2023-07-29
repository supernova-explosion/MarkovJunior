from __future__ import annotations
from numpy import ndarray
from rule_node import RuleNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from grid import Grid


class ParallelNode(RuleNode):
    """
    不是真的并行执行，只是每一步都互不影响，对某个位置的后续操作可能覆盖之前的操作（针对同一个rule，多个rule之间本身就是相互独立的）。
    行为类似AllNode，但AllNode考虑的情况更多，比如之前操作过的位置后续不允许再操作（针对同一个rule，多个rule之间本身就是相互独立的）。
    所以相对来说，如果不在乎操作是否会覆盖，则使用ParallelNode更高效。
    """

    def __init__(self) -> None:
        super().__init__()

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        # print("ParallelNode load")
        if not super().load(element, parent_symmetry, grid):
            return False
        self.new_state = [0] * len(self.grid.state)
        return True

    def add(self, r, x, y, z, maskr: ndarray):
        rule = self.rules[r]
        if self.ip.random.random() > rule.p:
            return
        self.last[r] = True
        mx, my = self.grid.mx, self.grid.my
        omx, omy, omz = rule.omx, rule.omy, rule.omz
        for dz in range(omz):
            for dy in range(omy):
                for dx in range(omx):
                    new_value = rule.output[dx + dy * omx + dz * omx * omy]
                    idi = x + dx + (y + dy) * mx + (z + dz) * mx * my
                    if new_value != 255 and new_value != self.grid.state[idi]:
                        self.new_state[idi] = new_value
                        self.ip.changes.append((x + dx, y + dy, z + dz))
        self.match_count += 1

    def go(self) -> bool:
        if not super().go():
            return False
        for n in range(self.ip.first[self.ip.counter], len(self.ip.changes)):
            x, y, z = self.ip.changes[n]
            i = x + y * self.grid.mx + z * self.grid.mx * self.grid.my
            self.grid.state[i] = self.new_state[i]
        self.counter += 1
        return self.match_count > 0
