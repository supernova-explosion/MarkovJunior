from grid import Grid
from lxml.etree import _Element
from branch import Branch


class MapNode(Branch):

    def __init__(self) -> None:
        pass

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        print("MapNode")
        return True


if __name__ == "__main__":
    text = "10 20 30 40 50"
    # 使用 split() 方法拆分字符串，并使用 map() 函数将子字符串转换为整数
    numbers = list(map(int, text.split()))
    print(numbers)  # 输出：[10, 20, 30, 40, 50]
