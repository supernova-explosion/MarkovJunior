from __future__ import annotations
import copy
from lxml.etree import _Element
from graphic import Graphic
from helper import Helper
from symmetry_helper import SymmetryHelper
from array_helper import ArrayHelper
from vox_helper import VoxHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from grid import Grid


class Rule:

    def __init__(self, input: list[int], imx, imy, imz, output: list[int], omx, omy, omz, c, p) -> None:
        self.input = input
        """input pattern，颜色位掩码数组"""

        self.output = output
        """output pattern，数组，通配符为255"""

        self.imx = imx
        self.imy = imy
        self.imz = imz
        self.omx = omx
        self.omy = omy
        self.omz = omz
        self.p = p
        self.original = False
        lists = []
        for i in range(c):
            lists.append([])
        for z in range(imz):
            for y in range(imy):
                for x in range(imx):
                    w = input[x + y * imx + z * imx * imy]
                    for i in range(c):
                        if w & 1 == 1:
                            lists[i].append((x, y, z))
                        w >>= 1
        self.ishifts = copy.deepcopy(lists)
        if omx == imx and omy == imy and omz == imz:
            list(map(list.clear, lists))
            for z in range(omz):
                for y in range(omy):
                    for x in range(omx):
                        o = output[x + y * omx + z * omx * omy]
                        if o != 255:
                            lists[o].append((x, y, z))
                        else:
                            for i in range(c):
                                lists[i].append((x, y, z))
            self.oshifts = copy.deepcopy(lists)
        wildcard = (1 << c) - 1
        binput = []
        for w in input:
            w = 255 if w == wildcard else Rule.first_non_zero_position(w)
            binput.append(w)

    def __members(self):
        return (frozenset(self.input), self.imx, self.imy, self.imz, frozenset(self.output), self.omz, self.omy, self.omz)

    def __eq__(self, other: Rule):
        return self.__members() == other.__members()

    def __hash__(self):
        return hash(self.__members())

    def z_rotated(self):
        new_input = [0] * len(self.input)
        for z in range(self.imz):
            for y in range(self.imx):
                for x in range(self.imy):
                    new_input[x + y * self.imy + z * self.imx * self.imy] = self.input[self.imx -
                                                                                       1 - y + x * self.imx + z * self.imx * self.imy]
        new_output = [0] * len(self.output)
        for z in range(self.omz):
            for y in range(self.omx):
                for x in range(self.omy):
                    new_output[x + y * self.omy + z * self.omx * self.omy] = self.output[self.omx -
                                                                                         1 - y + x * self.omx + z * self.omx * self.omy]
        return Rule(new_input, self.imy, self.imx, self.imz, new_output, self.omy, self.omx, self.omz, len(self.ishifts), self.p)

    def y_rotated(self):
        new_input = [0] * len(self.input)
        for z in range(self.imx):
            for y in range(self.imy):
                for x in range(self.imz):
                    new_input[x + y * self.imz + z * self.imz * self.imy] = self.input[self.imx -
                                                                                       1 - z + y * self.imx + x * self.imx * self.imy]
        new_output = [0] * len(self.output)
        for z in range(self.omx):
            for y in range(self.omy):
                for x in range(self.omz):
                    new_output[x + y * self.omz + z * self.omz * self.omy] = self.output[self.omx -
                                                                                         1 - z + y * self.omx + x * self.omx * self.omy]
        return Rule(new_input, self.imz, self.imy, self.imx, new_output, self.omz, self.omy, self.omx, len(self.ishifts), self.p)

    def reflected(self):
        new_input = [0] * len(self.input)
        for z in range(self.imz):
            for y in range(self.imy):
                for x in range(self.imx):
                    new_input[x + y * self.imx + z * self.imx * self.imy] = self.input[self.imx -
                                                                                       1 - x + y * self.imx + z * self.imx * self.imy]
        new_output = [0] * len(self.output)
        for z in range(self.omz):
            for y in range(self.omy):
                for x in range(self.omx):
                    new_output[x + y * self.omx + z * self.omx * self.omy] = self.output[self.omx -
                                                                                         1 - x + y * self.omx + z * self.omx * self.omy]
        return Rule(new_input, self.imx, self.imy, self.imz, new_output, self.omx, self.omy, self.omz, len(self.ishifts), self.p)

    def symmetries(self, symmetry, is_2d):
        return SymmetryHelper.square_symmetries(self, lambda r: r.z_rotated(), lambda r: r.reflected(), symmetry) if is_2d else 1

    @staticmethod
    def load_resource(file_name, legend, is_2d):
        if legend is None:
            print(f"no legend for {file_name}")
            return None, -1, -1, -1
        data, mx, my, mz = Graphic.load_bitmap(
            file_name) if is_2d else VoxHelper.load_vox(file_name)
        if data is None:
            print(f"couldn't read {file_name}")
            return None, -1, -1, -1
        ords, amount = Helper.ords(data)
        if amount > len(legend):
            print(
                f"the amount of colors {amount} in {file_name} is more than {len(legend)}")
        return [legend[ord] for ord in ords], mx, my, mz

    @staticmethod
    def parse(s: str):
        lines = [str.split("/") for str in s.split()]
        mx = len(lines[0][0])
        my = len(lines[0])
        mz = len(lines)
        result = [None] * mx * my * mz
        for z in range(mz):
            linesz = lines[mz - 1 - z]
            if len(linesz) != my:
                print("non-rectangular pattern", end="")
                return None, -1, -1, -1
            for y in range(my):
                linesy = linesz[y]
                if len(linesy) != mx:
                    print("non-rectangular pattern", end="")
                    return None, -1, -1, -1
                for x in range(mx):
                    result[x + y * mx + z * mx * my] = linesy[x]
        return result, mx, my, mz

    @classmethod
    def load(cls, element: _Element, gin: Grid, gout: Grid):
        line_number = element.sourceline
        is_2d = gin.mz == 1

        def file_path(name):
            result = "resources/rules/"
            if gout.folder is not None:
                file_path += gout.folder + "/"
            result += name
            result += ".png" if is_2d else ".vox"
            return result

        in_str = element.get("in")
        out_str = element.get("out")
        fin_str = element.get("fin")
        fout_str = element.get("fout")
        file_str = element.get("file")
        legend = element.get("legend")
        if file_str is None:
            if in_str is None and fin_str is None:
                print(f"no input in a rule at line {line_number}")
                return None
            if out_str is None and fout_str is None:
                print(f"no output in a rule at line {line_number}")
                return None
            in_rect, imx, imy, imz = Rule.parse(in_str) if in_str is not None else Rule.load_resource(
                file_path(fin_str), legend, is_2d)
            if in_rect is None:
                print(f" in input at line {line_number}")
                return None
            out_rect, omx, omy, omz = Rule.parse(out_str) if in_str is not None else Rule.load_resource(
                file_path(fout_str), legend, is_2d)
            if out_rect is None:
                print(f" in input at line {line_number}")
                return None
            if gin == gout and (omz != imz or omy != imy or omx != imx):
                print(f"non-matching pattern sizes at line {line_number}")
                return None
        else:
            if in_str is not None or fin_str is not None or out_str is not None or fout_str is not None:
                print(
                    f"rule at line {line_number} already contains a file attribute")
                return None
            rect, fx, fy, fz = Rule.load_resource(
                file_path(file_str), legend, is_2d)
            if rect is None:
                print(f" in a rule at line {line_number}")
            if fx % 2 != 0:
                print(f"odd width {fx} in {file_str}")
                return None
            imx = omx = fx / 2
            imy = omy = fy
            imz = omz = fz
            in_rect = ArrayHelper.flat_array_3d(
                fx / 2, fy, fz, lambda x, y, z: rect[x + y * fx + z * fx * fy])
            out_rect = ArrayHelper.flat_array_3d(
                fx / 2, fy, fz, lambda x, y, z: rect[x + fx / 2 + y * fx + z * fx * fy])
        input = []
        for c in in_rect:
            if c in gin.waves:
                input.append(gin.waves[c])
            else:
                print(
                    f"input code {c} at line {line_number} is not found in codes")
                return None
        output = []
        for c in out_rect:
            if c == "*":
                output.append(255)
            else:
                if c in gout.waves:
                    output.append(gout.values[c])
                else:
                    print(
                        f"output code {c} at line {line_number} is not found in codes")
                    return None
        p = element.get("p", 1.0)
        return cls(input, imx, imy, imz, output, omx, omy, omz, gin.c, p)

    @staticmethod
    def first_non_zero_position(i):
        for p in range(32):
            if (i & 1) == 1:
                return p
            i >>= 1
        return 255


if __name__ == "__main__":
    # data, x, y, z = Graphic.load_bitmap("resources/fonts/Tamzen8x16r.png")
    # result, count = Helper.ords(data)
    # print(result, count)
    a = [1, 2, 3]
    b = a[:]
    print(b)
    a[0] = 2
    print(a, b)
