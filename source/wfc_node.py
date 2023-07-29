from __future__ import annotations
import math
import time
import numpy as np
from abc import abstractmethod
from random import Random
from helper import Helper
from branch import Branch
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from numpy import ndarray
    from grid import Grid


class WFCNode(Branch):

    def __init__(self) -> None:
        super().__init__()
        self.DX = [1, 0, -1, 0, 0, 0]
        self.DY = [0, 1, 0, -1, 0, 0]
        self.DZ = [0, 0, 0, 0, 1, -1]
        self.P = 0
        self.weights = []
        self.propagator = []
        self.new_grid: Grid = None
        self.first_go = True
        self.map: dict = {}
        self.stack = []
        self.stack_size = 0
        self.periodic = False
        self.patterns = []

        self.name = None
        """包含训练此WFC模型的图块集或示例图像的资源文件的名称"""

        self.N = 1
        """图案的大小，对于TileModel，该值始终为 1。"""

        self.distribution = []
        self.random = None

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        print("WFCNode load")
        self.shannon = bool(element.get("shannon", False))
        self.tries = int(element.get("tries", 1000))
        self.wave = Wave(len(grid.state), self.P,
                         len(self.propagator), self.shannon)
        self.start_wave = Wave(len(grid.state), self.P,
                               len(self.propagator), self.shannon)
        # self.stack = [(0, 0)] * len(self.wave.data) * self.P
        self.stack = []
        self.sum_of_weights = 0
        self.sum_of_weight_log_weights = 0
        self.starting_entropy = 0
        if self.shannon:
            self.weight_log_weights = [0.0] * self.P
            for t in range(self.P):
                self.weight_log_weights[t] = self.weights[t] * \
                    math.log(self.weights[t])
                self.sum_of_weights += self.weights[t]
                self.sum_of_weight_log_weights += self.weight_log_weights[t]
            self.starting_entropy = math.log(
                self.sum_of_weights) - self.sum_of_weight_log_weights // self.sum_of_weights
        self.distribution = [0.0] * self.P
        return super().load(element, parent_symmetry, self.new_grid)

    def reset(self):
        super().reset()
        self.n = -1
        self.first_go = True

    def go(self) -> bool:
        if self.n > 0:
            return super().go()
        if self.first_go:
            self.wave.init(self.propagator, self.sum_of_weights,
                           self.sum_of_weight_log_weights, self.starting_entropy, self.shannon)
            for i in range(len(self.wave.data)):
                value = self.grid.state[i]
                if value in self.map:
                    start_wave = self.map[value]
                    for t in range(self.P):
                        if not start_wave[t]:
                            self.ban(i, t)
            # print("self.propagator", self.propagator)
            first_success = self.propagate()
            if not first_success:
                print("initial conditions are contradictive")
                return False
            self.start_wave.copy_from(
                self.wave, len(self.propagator), self.shannon)
            good_seed = self.good_seed()
            if good_seed is None:
                return False
            self.random = Random(good_seed)
            self.stack = []
            # self.stack_size = 0
            self.wave.copy_from(self.start_wave, len(
                self.propagator), self.shannon)
            self.first_go = False
            self.new_grid.clear()
            self.ip.grid = self.new_grid
            return True
        else:
            node = self.next_unobserved_node(self.random)
            if node >= 0:
                self.observe(node, self.random)
                self.propagate()
            else:
                self.n += 1
            if self.n >= 0 or self.ip.gif:
                self.update_state()
            return True

    def good_seed(self):
        """尝试找到WFC算法完成时不会出现矛盾的随机种子，即“好”种子。"""
        for k in range(self.tries):
            observations_so_far = 0
            seed = self.ip.random.random()
            local_random = Random(seed)
            self.stack = []
            # self.stack_size = 0
            self.wave.copy_from(self.start_wave, len(
                self.propagator), self.shannon)
            while True:
                node = self.next_unobserved_node(local_random)
                if node >= 0:
                    self.observe(node, local_random)
                    observations_so_far += 1
                    success = self.propagate()
                    if not success:
                        print(
                            f"CONTRADICTION on try {k} with {observations_so_far} observations")
                        break
                else:
                    print(
                        f"wfc found a good seed {seed} on try {k} with {observations_so_far} observations")
                    return seed
        print(f"wfc failed to find a good seed in {self.tries} tries")
        return None

    def next_unobserved_node(self, local_random: Random):
        """查找具有多种可能模式的位置，优先选择最受约束的位置。如果不存在这样的位置，则返回-1，表示WFC算法已完成。"""
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        min = 1E+4
        argmin = -1
        for z in range(mz):
            for y in range(my):
                for x in range(mx):
                    if not self.periodic and (x + self.N > mx or y + self.N > my or z + 1 > mz):
                        continue
                    i = x + y * mx + z * mx * my
                    remaining_values = self.wave.sums_of_ones[i]
                    entropy = self.wave.entropies[i] if self.shannon else remaining_values
                    if remaining_values > 1 and entropy <= min:
                        noise = 1E-6 * local_random.random()
                        if entropy + noise < min:
                            min = entropy + noise
                            argmin = i
        return argmin

    def observe(self, node, local_random: Random):
        w = self.wave.data[node]
        for t in range(self.P):
            self.distribution[t] = self.weights[t] if w[t] else 0.0
        r = Helper.random(self.distribution, local_random.random())
        for t in range(self.P):
            if w[t] != (t == r):
                self.ban(node, t)

    def propagate(self):
        mx, my, mz = self.grid.mx, self.grid.my, self.grid.mz
        # while self.stack_size > 0:
        while self.stack:
            i1, p1 = self.stack.pop()
            # i1, p1 = self.stack[self.stack_size]
            # self.stack_size -= 1
            x1 = i1 % mx
            y1 = i1 % (mx * my) // mx
            z1 = i1 // (mx * my)
            for d in range(len(self.propagator)):
                dx, dy, dz = self.DX[d], self.DY[d], self.DZ[d]
                x2, y2, z2 = x1 + dx, y1 + dy, z1 + dz
                if not self.periodic and (x2 < 0 or y2 < 0 or z2 < 0 or x2 + self.N > mx or y2 + self.N > my or z2 + 1 > mz):
                    continue
                if x2 < 0:
                    x2 += mx
                elif x2 >= mx:
                    x2 -= mx
                if y2 < 0:
                    y2 += my
                elif y2 >= my:
                    y2 -= my
                if z2 < 0:
                    z2 += mz
                elif z2 >= mz:
                    z2 -= mz
                i2 = x2 + y2 * mx + z2 * mx * my
                p = self.propagator[d][p1]
                compat = self.wave.compatible[i2]
                for t2 in p:
                    comp = compat[t2]
                    comp[d] -= 1
                    if comp[d] == 0:
                        self.ban(i2, t2)
        return self.wave.sums_of_ones[0] > 0

    def ban(self, i, t):
        wave = self.wave
        wave.data[i, t] = False
        comp = wave.compatible[i, t]
        for d in range(len(self.propagator)):
            comp[d] = 0
        self.stack.append((i, t))
        # self.stack[self.stack_size] = (i, t)
        # self.stack_size += 1
        wave.sums_of_ones[i] -= 1
        if self.shannon:
            sum = wave.sums_of_weights[i]
            wave.entropies[i] += wave.sums_of_weight_log_weights[i] // sum - \
                math.log(sum)
            wave.sums_of_weights[i] -= self.weights[t]
            wave.sums_of_weight_log_weights[i] -= self.weight_log_weights[t]
            sum = wave.sums_of_weights[i]
            if sum == 0:
                if wave.sums_of_weight_log_weights[i] == 0:
                    wave.entropies[i] = float("nan")
                elif wave.sums_of_weight_log_weights[i] > 0:
                    wave.entropies[i] = float("-inf")
                elif wave.sums_of_weight_log_weights[i] < 0:
                    wave.entropies[i] = float("inf")
            else:
                wave.entropies[i] -= wave.sums_of_weight_log_weights[i] // sum - \
                    math.log(sum)

    @abstractmethod
    def update_state(self):
        pass


class Wave:

    def __init__(self, length, P, D, shannon) -> None:
        self.opposite = [2, 3, 0, 1, 5, 4]
        self.data = np.full((length, P), True)
        self.compatible = np.full((length, P, D), -1)
        self.sums_of_ones = [0] * length
        if shannon:
            self.sums_of_weights = [0.0] * length
            self.sums_of_weight_log_weights = [0.0] * length
            self.entropies = [0.0] * length

    def init(self, propagator: list, sums_of_weights, sums_of_weight_log_weights, starting_entropy, shannon):
        P = len(self.data[0])
        for i, datai in enumerate(self.data):
            for p in range(P):
                datai[p] = True
                for d in range(len(propagator)):
                    self.compatible[i, p, d] = len(
                        propagator[self.opposite[d]][p])
            self.sums_of_ones[i] = P
            if shannon:
                self.sums_of_weights[i] = sums_of_weights
                self.sums_of_weight_log_weights[i] = sums_of_weight_log_weights
                self.entropies[i] = starting_entropy

    def copy_from(self, wave: Wave, D, shannon):
        for i, datai in enumerate(self.data):
            wave_datai = wave.data[i]
            for t in range(len(datai)):
                datai[t] = wave_datai[t]
                for d in range(D):
                    self.compatible[i, t, d] = wave.compatible[i, t, d]
            self.sums_of_ones[i] = wave.sums_of_ones[i]
            if shannon:
                self.sums_of_weights[i] = wave.sums_of_weights[i]
                self.sums_of_weight_log_weights[i] = wave.sums_of_weight_log_weights[i]
                self.entropies[i] = wave.entropies[i]


if __name__ == "__main__":
    print(math.log(0))
