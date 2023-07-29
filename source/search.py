from __future__ import annotations
import random
import numpy as np
from queue import PriorityQueue
from helper import Helper
from observation import Observation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rule import Rule
    from random import Random


class Search:

    @staticmethod
    def run(present: list[int], future: list[int], rules: list[Rule], mx, my, mz, c, node, limit, depth_coefficient, seed) -> list[Board]:
        """
        尝试找到网格状态的轨迹，从当前状态开始，到匹配未来状态结束。轨迹中的每个状态都是将给定规则之一应用于前一个状态的结果。
        轨迹为网格状态列表，如果未找到轨迹则为None，当前状态不包含在轨迹中。
        """
        from all_node import AllNode
        is_all_node = isinstance(node, AllNode)
        bpotentials = np.full((c, len(present)), -1)
        fpotentials = np.full((c, len(present)), -1)
        Observation.compute_backward_potentials(
            bpotentials, future, mx, my, mz, rules)
        root_backward_estimate = Observation.backward_pointwise(
            bpotentials, present)
        Observation.compute_forward_potentials(
            fpotentials, present, mx, my, mz, rules)
        root_forward_estimate = Observation.forward_pointwise(
            fpotentials, future)
        if root_backward_estimate < 0 or root_forward_estimate < 0:
            print("incorrect problem")
            return None
        print(
            f"root estimate = ({root_backward_estimate}, {root_forward_estimate})")
        if root_backward_estimate == 0:
            return []
        root_board = Board(
            present, -1, 0, root_backward_estimate, root_forward_estimate)
        database = [root_board]
        visited = {tuple(present): 0}
        frontier = PriorityQueue()
        local_random = random.Random(seed)
        frontier.put((root_board.rank(local_random, depth_coefficient), 0))
        record = root_backward_estimate + root_forward_estimate
        while frontier and (limit < 0 or len(database) < limit):
            _, parent_index = frontier.get()
            parent_board = database[parent_index]
            children = Search.all_child_states(parent_board.state, mx, my, rules) if is_all_node else Search.one_child_states(
                parent_board.state, mx, my, rules)
            for child_state in children:
                if child_state in visited:
                    child_index = visited[child_state]
                    old_board = database[child_index]
                    if (parent_board.depth + 1) < old_board.depth:
                        old_board.depth = parent_board.depth + 1
                        old_board.parent_index = parent_index
                        if old_board.backward_estimate >= 0 and old_board.forward_estimate >= 0:
                            frontier.put(
                                (old_board.rank(local_random, depth_coefficient), child_index))
                else:
                    child_backward_estimate = Observation.backward_pointwise(
                        bpotentials, child_state)
                    Observation.compute_forward_potentials(
                        fpotentials, child_state, mx, my, mz, rules)
                    child_forward_estimate = Observation.forward_pointwise(
                        fpotentials, future)
                    if child_backward_estimate < 0 or child_forward_estimate < 0:
                        continue
                    child_board = Board(child_state, parent_index, parent_board.depth +
                                        1, child_backward_estimate, child_forward_estimate)
                    database.append(child_board)
                    child_index = len(database) - 1
                    visited[(child_board.state)] = child_index
                    if child_board.forward_estimate == 0:
                        print(
                            f"found a trajectory of length {parent_board.depth + 1}, visited {len(visited)} states")
                        trajectory = Board.trajectory(child_index, database)
                        trajectory.reverse()
                        return [b.state for b in trajectory]
                    else:
                        if limit < 0 and (child_backward_estimate + child_forward_estimate) <= record:
                            record = child_backward_estimate + child_forward_estimate
                            print(
                                f"found a state of record estimate {record} = {child_backward_estimate} + {child_forward_estimate}")
                            frontier.put(
                                (child_board.rank(local_random, depth_coefficient), child_index))
        return None

    @staticmethod
    def matches(rule: Rule, x, y, state: list[int], mx, my):
        """判断此规则在给定网格状态中的位置(x, y)处是否匹配"""
        if (x + rule.imx) > mx or (y + rule.imy) > my:
            return False
        dx = dy = 0
        for v in rule.input:
            if (v & (1 << state[x + dx + (y + dy) * mx])) == 0:
                return False
            dx += 1
            if dx == rule.imx:
                dx = 0
                dy += 1
        return True

    @staticmethod
    def applied(rule: Rule, x, y, state: list[int], mx):
        """将规则应用于位置(x, y)，返回一个新状态"""
        result = state[:]
        for dz in range(rule.omz):
            for dy in range(rule.omy):
                for dx in range(rule.omx):
                    new_value = rule.output[dx + dy *
                                            rule.omx + dz * rule.omx * rule.omy]
                    if new_value != 255:
                        result[x + dx + (y + dy) * mx] = new_value
        return result

    @staticmethod
    def is_inside(p: tuple[int, int], rule: Rule, x, y):
        """判断此(x, y)元组是否位于给定规则的输入模式内的给定位置"""
        return x < p[0] and p[0] < (x + rule.imx) and y < p[1] and p[1] < (y + rule.imy)

    @staticmethod
    def overlap(rule0: Rule, x0, y0, rule1: Rule, x1, y1):
        """判断两个规则的输入模式在给定位置是否重叠"""
        for dy in range(rule0.imy):
            for dx in range(rule0.imx):
                if Search.is_inside((x0 + dx, y0 + dy), rule1, x1, y1):
                    return True
        return False

    @staticmethod
    def one_child_states(state: list[int], mx, my, rules: list[Rule]):
        """对one节点执行给定规则，返回可以从该状态一步到达的状态列表。"""
        result = []
        for rule in rules:
            for y in range(my):
                for x in range(mx):
                    if Search.matches(rule, x, y, state, mx, my):
                        result.append(Search.applied(rule, x, y, state, mx))
        return result

    @staticmethod
    def all_child_states(state: list[int], mx, my, rules: list[Rule]):
        """对all节点执行给定规则，返回可以从该状态一步到达的状态列表。"""
        tiles = []
        amounts = [0] * len(state)
        for i in range(len(state)):
            x = i % mx
            y = i // mx
            for rule in rules:
                if Search.matches(rule, x, y, state, mx, my):
                    tiles.append((rule, i))
                    for dy in range(rule.imy):
                        for dx in range(rule.imx):
                            amounts[x + dx + (y + dy) * mx] += 1
        mask = np.full(len(tiles), True)
        solution = []
        result = []
        Search.enumerate(result, solution, tiles, amounts, mask, state, mx)
        return result

    @staticmethod
    def enumerate(children: list[int], solution: list[tuple[Rule, int]], tiles: list[tuple[Rule, int]], amounts: list[int], mask: list[bool], state: list[int], mx):
        """通过递归回溯搜索，查找并应用all节点的规则的所有最大非重叠匹配集。"""
        index = Helper.max_positive_index(amounts)
        x = index % mx
        y = index // mx
        if index < 0:
            children.append(Search.apply(solution, mx))
            return
        cover = []
        for l, rule, i in tiles:
            if mask[l] and Search.is_inside((x, y), rule, i % mx, i // mx):
                cover.append((rule, i))
        for rule, i in cover:
            solution.append((rule, i))
            intersecting = []
            for l, rule1, i1 in tiles:
                if Search.overlap(rule, i % mx, i // mx, rule1, i1 % mx, i1 // mx):
                    intersecting.append(l)
            for l in intersecting:
                Search.hide(l, False, tiles, amounts, mask, mx)
            Search.enumerate(children, solution, tiles,
                             amounts, mask, state, mx)
            for l in intersecting:
                Search.hide(l, True, tiles, amounts, mask, mx)
            solution.pop()

    @staticmethod
    def hide(l, unhide, tiles: list[tuple[Rule, int]], amounts: list[int], mask: list[bool], mx):
        mask[l] = unhide
        rule, i = tiles[l]
        x = i % mx
        y = i // mx
        incr = 1 if unhide else -1
        for dy in range(rule.imy):
            for dx in range(rule.imx):
                amounts[x + dx + (y + dy) * mx] = incr

    @staticmethod
    def apply(state: list[int], solution: list[tuple[Rule, int]], mx):
        """将一组不重叠的规则应用于此网格状态，返回新的网格状态。"""
        result = state[:]
        for rule, i in solution:
            Search.apply_rule(rule, i % mx, i // mx, result, mx)
        return result

    @staticmethod
    def apply_rule(rule: Rule, x, y, state: list[int], mx):
        for dy in range(rule.omy):
            for dx in range(rule.omx):
                c = rule.output[dx + dy * rule.omx]
                if c != 255:
                    state[x + dx + (y + dy) * mx] = c


class Board:

    def __init__(self, state: list[int], parent_index, depth, backward_estimate, forward_estimate) -> None:
        self.state = state
        self.parent_index = parent_index
        self.depth = depth
        self.backward_estimate = backward_estimate
        self.forward_estimate = forward_estimate

    def rank(self, random: Random, depth_coefficient):
        result = 1000 - self.depth if depth_coefficient < 0 else self.forward_estimate + \
            self.backward_estimate + 2 * depth_coefficient * self.depth
        return result + 0.0001 * random.random()

    @staticmethod
    def trajectory(index, database: list[Board]) -> list[Board]:
        """计算database中给定索引的网格状态轨迹，返回一个倒序列表"""
        result = []
        board = database[index]
        while board.parent_index >= 0:
            result.append(board)
            board = database[board.parent_index]
        return result


if __name__ == "__main__":
    q = PriorityQueue()
    q.put((0.1, "a"))
    q.put((0.0, "b"))
    q.put((0.2, "c"))
    _, a = q.get()
    print(a)
