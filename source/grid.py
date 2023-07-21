from lxml.etree import _Element
from rule import Rule


class Grid:

    def __init__(self, element: _Element, mx, my, mz) -> None:
        self.mx = mx
        self.my = my
        self.mz = mz
        self.c = 0

        self.values = {}
        """颜色字符与索引的map"""

        self.waves = {}
        self.characters = []
        """表示颜色的字符列表"""

        self.transparent = None
        self.state = []
        self.state_buffer = []
        self.mask = []
        self.folder = None
        self.load(element)

    def load(self, element: _Element):
        str_values = element.get("values")
        color_string = str_values.replace(" ", "") if str_values else None
        if color_string is None:
            raise Exception("no values specified")
        self.c = len(color_string)
        size = self.mx * self.my * self.mz
        self.state = [0] * size
        self.state_buffer = [0] * size
        self.mask = [False] * size
        for i, symbol in enumerate(color_string):
            if symbol in self.waves:
                raise Exception(f"repeating value \"{symbol}\"")
            self.characters.append(symbol)
            self.values[symbol] = i
            self.waves[symbol] = 1 << i
        transparent_str = element.get("transparent")
        if transparent_str is not None:
            self.transparent = self.wave(transparent_str)
        unions = element.xpath(
            ".//*[self::markov or self::sequence or self::union]//union")
        self.waves["*"] = (1 << self.c) - 1
        for union in unions:
            symbol = union.get("symbol")
            if symbol in self.waves:
                raise Exception(f"repeating union type \"{symbol}\"")
            w = self.wave(union.get("values"))
            self.waves[symbol] = w
        self.folder = element.get("folder")

    def clear(self):
        self.state = [0] * len(self.state)

    def wave(self, values):
        """将颜色字符串解析为bitmask"""
        sum = 0
        for v in values:
            sum += 1 << self.values[v]
        return sum

    def matches(self, rule: Rule, x, y, z) -> bool:
        dz, dy, dx = 0, 0, 0
        for item in rule.input:
            if (item & (1 << self.state[x + dx + (y + dy) * self.mx + (z + dz) * self.mx * self.my])) == 0:
                return False
            dx += 1
            if dx == rule.imx:
                dx = 0
                dy += 1
                if dy == rule.imy:
                    dy = 0
                    dz += 1
        return True


if __name__ == "__main__":
    a = [1, 2, 3, 4]
    print()
