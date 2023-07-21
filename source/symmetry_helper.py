import numpy as np


class SymmetryHelper:

    square_subgroups = {
        "()": [True, False, False, False, False, False, False, False],
        "(x)": [True, True, False, False, False, False, False, False],
        "(y)": [True, False, False, False, False, True, False, False],
        "(x)(y)": [True, True, False, False, True, True, False, False],
        "(xy+)": [True, False, True, False, True, False, True, False],
        "(xy)": [True, True, True, True, True, True, True, True]
    }

    cube_subgroups = {
        "()": [i == 0 for i in range(48)],
        "(x)": [i == 0 or i == 1 for i in range(48)],
        "(z)": [i == 0 or i == 17 for i in range(48)],
        "(xy)": [i < 8 for i in range(48)],
        "(xyz+)": [i % 2 == 0 for i in range(48)],
        "(xyz)": [True for i in range(48)]
    }

    @staticmethod
    def square_symmetries(thing, rotation, reflection, subgroup=None):
        things = [None] * 8
        things[0] = thing                  # e
        things[1] = reflection(things[0])  # b
        things[2] = rotation(things[0])    # a
        things[3] = reflection(things[2])  # ba
        things[4] = rotation(things[2])    # a2
        things[5] = reflection(things[4])  # ba2
        things[6] = rotation(things[4])    # a3
        things[7] = reflection(things[6])  # ba3
        result = set()
        for i, v in enumerate(things):
            if subgroup is None or subgroup[i]:
                result.add(v)
        return result

    @staticmethod
    def get_symmetry(is_2d, s, default) -> list[bool]:
        if s is None:
            return default
        result = SymmetryHelper.square_subgroups.get(
            s) if is_2d else SymmetryHelper.cube_subgroups.get(s)
        return result


if __name__ == "__main__":
    # print(SymmetryHelper.get_symmetry(True, "(a)", None))
    # print(SymmetryHelper.cube_subgroups)
    a = (1, 2, 3)
    b = (1, 2, 3)
    c = set()
    c.add(a)
    c.add(b)
    print(c)
