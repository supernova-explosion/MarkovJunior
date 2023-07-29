from __future__ import annotations
from node import Node
from graphic import Graphic
from helper import Helper
from symmetry_helper import SymmetryHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from grid import Grid


class ConvChainNode(Node):
    """
    ConvChainNode在网格的一部分上运行ConvChain算法。该算法尝试用两种颜色（通常是“黑色”和“白色”）替换substrate单元格，
    使得“黑色”和“白色”单元格局部形成样本图像中出现的图案。如果网格不包含substrate单元格，则ConvChainNode节点不适用。
    非substrate单元格在算法中保持不变，但可能有助于图案的“局部相似性”。
    最初在网格中的“黑色”和“白色”单元格将被视为图案的一部分，其他非substrate颜色将被视为“黑色”，图案可能会环绕网格边界。
    """

    def __init__(self) -> None:
        self.counter = 0

    def load(self, element: _Element, symmetry: list[bool], grid: Grid) -> bool:
        if self.grid.mz != 1:
            print("ConvChain currently works only for 2d")
            return False
        name = element.get("sample")
        file_name = f"resources/samples/{name}.png"
        bitmap, smx, smy, _ = Graphic.load_bitmap(file_name)
        if not bitmap:
            print(f"couldn't load ConvChain sample {file_name}")
            return False

        # 0xffffffff = 2 ** 32 - 1 = 白色
        self.sample = [b == 0xffffffff for b in bitmap]
        """样本图转换为布尔数组，True代表白色，False代表黑色"""

        self.n = int(element.get("n", 3))
        self.steps = int(element.get("steps", -1))
        self.temperature = float(element.get("temperature", 1.0))
        self.c0 = self.grid.values[element.get("black")]
        self.c1 = self.grid.values[element.get("white")]
        self.substrate_color = self.grid.values[element.get("on")]
        self.substrate = [False] * len(self.grid.state)
        self.weights = [0.0] * (1 << (self.n * self.n))
        for y in range(smy):
            for x in range(smx):
                # 对样本空间采样
                pattern = Helper.pattern(lambda dx, dy: self.sample[(
                    x + dx) % smx + (y + dy) % smy * smx], self.n)
                symmetries = SymmetryHelper.square_symmetries(pattern, lambda q: Helper.rotated(
                    q, self.n), lambda q: Helper.reflected(q, self.n), lambda q1, q2: False, symmetry)
                for q in symmetries:
                    self.weights[Helper.index(q)] += 1
        for i, v in enumerate(self.weights):
            if v <= 0:
                self.weights[i] = 0.1
        return True

    def toggle(self, state: list[int], i):
        """索引 i 处的网格状态在 c0 和 c1 两种颜色之间切换"""
        state[i] = self.c1 if state[i] == self.c0 else self.c0

    def go(self) -> bool:
        if self.steps > 0 and self.counter >= self.steps:
            return False
        mx, my = self.grid.mx, self.grid.my
        state = self.grid.state
        if self.counter == 0:
            any_substrate = False
            for i in range(len(self.substrate)):
                if state[i] == self.substrate_color:
                    state[i] = self.c0 if self.ip.random.randint(
                        0, 1) == 0 else self.c1
                    self.substrate[i] = True
                    any_substrate = True
            self.counter += 1
            return any_substrate
        for _ in state:
            r = self.ip.random.randrange(0, len(state))
            if not self.substrate[r]:
                continue
            x = r % mx
            y = r // mx
            q = 1.0
            for sy in range(y - self.n + 1, y + self.n):
                for sx in range(x - self.n + 1, x + self.n):
                    ind = difference = 0
                    for dy in range(self.n):
                        for dx in range(self.n):
                            X = sx + dx
                            if X < 0:
                                X += mx
                            elif X >= mx:
                                X -= mx
                            Y = sy + dy
                            if Y < 0:
                                Y += my
                            elif Y >= my:
                                Y -= my
                            value = state[X + Y * mx] == self.c1
                            power = 1 << (dy * self.n + dx)
                            ind += power if value else 0
                            if X == x and Y == y:
                                difference = power if value else -power
                    q *= self.weights[ind - difference] // self.weights[ind]
            if q >= 1:
                self.toggle(state, r)
                continue
            if self.temperature != 1:
                q = q ** (1.0 / self.temperature)
            if q > self.ip.random.random():
                self.toggle(state, r)
        self.counter += 1
        return True


if __name__ == "__main__":
    print(0xffffffff)
