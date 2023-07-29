from __future__ import annotations
import numpy as np
from numpy import ndarray
from node import Node
from rule import Rule
from field import Field
from search import Search
from observation import Observation
from symmetry_helper import SymmetryHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid
    from lxml.etree import _Element


class RuleNode(Node):

    def __init__(self) -> None:
        self.rules: list[Rule] = []
        self.last = []
        self.fields: list[Field] = None
        self.observations = None
        self.search = False
        self.limit = 0
        self.depth_coefficient = 0.0

        self.future_computed = False
        """是否已计算由该节点的observations确定的轨迹或向后电位。如果没有observations，则该标志无关紧要。"""

        self.last_matched_turn = 0
        """上次匹配的轮次，用于跟踪应重新扫描网格中的更改以查找匹配项。如果自上次全网格扫描以来该节点已重置，则 last_matched_turn 为 -1"""

        self.counter = 0
        """此节点已执行的次数(重置会刷新)"""

        self.future = []
        """
        如果节点存在observe，那么这个数组表示由这些观测结果确定的未来目标。
        每个元素都是颜色的bitmask，当网格中的每个单元格匹配响应的bitmask时，目标就达到了。
        """

        self.steps = 0
        """此节点可执行的最大次数(非累计，重置会刷新计数)，如果为0，则无限制"""

        self.temperature = 0.0
        self.potentials = None

        self.matches = []
        """
        (r, x, y, z)元组列表，其中规则r在网格中的位置(x, y, z)处匹配。该列表包含所有当前匹配项，但也可能包含一些过时的匹配项。
        为了避免过度分配和释放，列表永远不会被缩短，match_count字段是列表的真实长度。
        所有当前匹配都发生在该索引之前，除非这是OneNode，否则不会出现过时的匹配。
        """

        self.match_count = 0
        """
        matches的真实长度，实际列表长度可能大于match_count，所有当前匹配都发生在matches列表中的该索引之前。
        如果这是一个OneNode，那么该列表还可能在此索引之前包含一些过时的匹配项，因此该字段只是当前匹配项数量的最大值。
        """

        self.match_mask = None
        """
        将每个rule映射到一个二维numpy布尔数组，与matches列表中的元素对应。
        当且仅当(r, x, y, z)位于列表中match_count索引之前时，match_mask[r][x + y * mx + z * mx * my]为True。
        """

        self.trajectory = None
        """通过搜索找到的状态列表。当执行该节点时，轨迹中预先计算的状态将被复制到网格中，而不是像平常一样应用重写规则"""

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        # print("RuleNode load")
        symmetry_str = element.get("symmetry")
        symmetry = SymmetryHelper.get_symmetry(
            grid.mz == 1, symmetry_str, parent_symmetry)
        if symmetry is None:
            print(
                f"unknown symmetry \"{symmetry_str}\" at line {element.sourceline}")
            return False
        xrules = element.findall("rule")
        rule_elements = xrules if xrules else [element]
        for rule_element in rule_elements:
            rule = Rule.load(rule_element, grid, grid)
            if rule is None:
                print(f"rule is none at line {rule_element.sourceline}")
                return False
            rule.original = True
            is_2d = grid.mz == 1
            rule_symmetry_str = rule_element.get("symmetry")
            rule_symmetry = SymmetryHelper.get_symmetry(
                is_2d, rule_symmetry_str, symmetry)
            if rule_symmetry is None:
                print(
                    f"unknown symmetry {rule_symmetry_str} at line {rule_element.sourceline}")
                return False
            for r in rule.symmetries(rule_symmetry, is_2d):
                self.rules.append(r)
        self.last = [False] * len(self.rules)
        self.steps = int(element.get("steps", 0))
        self.temperature = float(element.get("temperature", 0.0))
        self.match_mask = np.full(
            (len(self.rules), len(self.grid.state)), False)
        color_count = grid.c
        state_length = len(grid.state)
        field_elements: list[_Element] = element.findall("field")
        if field_elements:
            self.fields = [None] * color_count
            self.potentials = np.zeros((color_count, state_length))
            for field_element in field_elements:
                c = field_element.get("for")
                if c in grid.values:
                    self.fields[grid.values[c]] = Field(field_element, grid)
                else:
                    print(
                        f"unknown field value {c} at line {element.sourceline}")
                    return False
        observe_elements: list[_Element] = element.findall("observe")
        if observe_elements:
            self.observations = [None] * color_count
            for x in observe_elements:
                value = x.get("value")
                index = grid.values[value]
                self.observations[index] = Observation(
                    x.get("from", value), x.get("to"), grid)
            self.search = bool(element.get("search", False))
            if self.search:
                self.limit = int(element.get("limit", -1))
                self.depth_coefficient = float(
                    element.get("depthCoefficient", 0.5))
            else:
                self.potentials = np.zeros((color_count, state_length))
            self.future = [0] * state_length
        return True

    def reset(self):
        self.last_matched_turn = -1
        self.counter = 0
        self.future_computed = False
        self.last = [False] * len(self.last)

    def add(self, r, x, y, z, maskr: ndarray):
        """当grid与rule匹配时，会调用此方法，各个rule之间的mask相互独立"""
        maskr[x + y * self.grid.mx + z * self.grid.mx * self.grid.my] = True
        match = (r, x, y, z)
        if self.match_count < len(self.matches):
            self.matches[self.match_count] = match
        else:
            self.matches.append(match)
        self.match_count += 1

    def go(self) -> bool:
        print("RuleNode go")
        self.last = [False] * len(self.last)
        if self.steps > 0 and self.counter >= self.steps:
            return False
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        if self.observations and not self.future_computed:
            if not Observation.compute_future_set_present(self.future, self.grid.state, self.observations):
                return False
            else:
                self.future_computed = True
                if self.search:
                    self.trajectory = None
                    tries = 1 if self.limit < 0 else 20
                    k = 0
                    while k < tries and self.trajectory is None:
                        self.trajectory = Search.run(
                            self.grid.state, self.future, self.rules, self.grid.mx, self.grid.my, self.grid.mz, self, self.limit, self.depth_coefficient, self.ip.random.random())
                        k += 1
                    if self.trajectory is None:
                        print("search returned none")
                else:
                    Observation.compute_backward_potentials(
                        self.potentials, self.future, mx, my, mz, self.rules)
        if self.last_matched_turn >= 0:
            for n in range(self.ip.first[self.last_matched_turn], len(self.ip.changes)):
                x, y, z = self.ip.changes[n]
                value = self.grid.state[x + y * mx + z * mx * my]
                for r, rule in enumerate(self.rules):
                    maskr = self.match_mask[r]
                    shifts = rule.ishifts[value]
                    for shiftx, shifty, shiftz in shifts:
                        sx = x - shiftx
                        sy = y - shifty
                        sz = z - shiftz
                        # 边界情况
                        if sx < 0 or sy < 0 or sz < 0 or (sx + rule.imx) > mx or (sy + rule.imy) > my or (sz + rule.imz) > mz:
                            continue
                        si = sx + sy * mx + sz * mx * my
                        # maskr避免重复添加相同位置
                        if not maskr[si] and self.grid.matches(rule, sx, sy, sz):
                            self.add(r, sx, sy, sz, maskr)
        else:
            self.match_count = 0
            for r, rule in enumerate(self.rules):
                maskr = self.match_mask[r]
                for z in range(rule.imz - 1, mz, rule.imz):
                    for y in range(rule.imy - 1, my, rule.imy):
                        for x in range(rule.imx - 1, mx, rule.imx):
                            value = self.grid.state[x + y * mx + z * mx * my]
                            shifts = rule.ishifts[value]
                            for shiftx, shifty, shiftz in shifts:
                                sx = x - shiftx
                                sy = y - shifty
                                sz = z - shiftz
                                # 边界情况
                                if sx < 0 or sy < 0 or sz < 0 or (sx + rule.imx) > mx or (sy + rule.imy) > my or (sz + rule.imz) > mz:
                                    continue
                                if self.grid.matches(rule, sx, sy, sz):
                                    self.add(r, sx, sy, sz, maskr)
        if self.fields is not None:
            any_success = any_computation = False
            for c, field in enumerate(self.fields):
                if field is not None and (self.counter == 0 or field.recompute):
                    success = field.compute(self.potentials[c], self.grid)
                    if not success and field.essential:
                        return False
                    any_success |= success
                    any_computation = True
            if any_computation and not any_success:
                return False
        return True


if __name__ == "__main__":
    a = [1, 2, 3, 4]
