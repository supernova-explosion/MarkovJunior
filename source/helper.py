import numpy as np


class Helper:

    @staticmethod
    def ords(data):
        result = []
        uniques = []
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


if __name__ == "__main__":
    arr = np.array([[2, 7, 1], [9, 14, 5]])
    max_index_1d = np.argmax(arr)
    print(max_index_1d)
