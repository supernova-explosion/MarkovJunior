import numpy as np
from lxml.etree import _Element


class Helper:

    @staticmethod
    def ords(data, uniques=None):
        if uniques is None:
            uniques = []
        result = []
        for d in data:
            if d in uniques:
                ord = uniques.index(d)
            else:
                ord = len(uniques)
                uniques.append(d)
            result.append(ord)
        return result, len(uniques)

    @staticmethod
    def max_positive_index(amounts: list[int]):
        """返回数组中最大正数的索引，如果数组不包含正数，则返回-1"""
        max = np.max(amounts)
        if max <= 0:
            return -1
        return np.argmax(amounts)

    @staticmethod
    def pattern(f, n):
        result = [None] * n * n
        for y in range(n):
            for x in range(n):
                result[x + y * n] = f(x, y)
        return result

    @staticmethod
    def rotated(p, n):
        return __class__.pattern(lambda x, y: p[n - 1 - y + x * n], n)

    @staticmethod
    def reflected(p, n):
        return __class__.pattern(lambda x, y: p[n - 1 - x + y * n], n)

    @staticmethod
    def index(array: list[bool]):
        """将布尔数组作为二进制位解析为int值，但这个执行顺序好像是反的"""
        result = 0
        power = 1
        for b in array:
            if b:
                result += power
            power *= 2
        return result

    @staticmethod
    def index(array: list[int], C):
        """将数组解析为一个int值，基数为C"""
        result = 0
        power = 1
        for i in range(len(array)):
            result += array[len(array) - 1 - i] * power
            power *= C
        return result

    @staticmethod
    def random(weights: list[float], r):
        sum = 0
        for weight in weights:
            sum += weight
        threshold = r * sum
        partial_sum = 0
        for i, weight in enumerate(weights):
            partial_sum += weight
            if partial_sum >= threshold:
                return i
        return 0

    @staticmethod
    def descendants(element: _Element, tags):
        queue = [element]
        while queue:
            e = queue.pop(0)
            if e != element:
                yield e
            for x in e.xpath(tags):
                queue.append(x)


if __name__ == "__main__":
    from vox_helper import VoxHelper
    name = "resources/rules/CarmaTower/side_13x5.vox"
    a, _, _, _ = VoxHelper.load_vox(name)
    b, c = Helper.ords(a)
    print(c)
