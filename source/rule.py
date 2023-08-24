from __future__ import annotations
from graphic import Graphic
from helper import Helper
from symmetry_helper import SymmetryHelper
from array_helper import ArrayHelper
from vox_helper import VoxHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element
    from grid import Grid


class Rule:

    def __init__(self, input: list[int], imx, imy, imz, output: list[int], omx, omy, omz, c, p, in_str=None, out_str=None) -> None:
        self.in_str = in_str
        self.out_str = out_str

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
        ishifts = []
        for i in range(c):
            ishifts.append([])
        for z in range(imz):
            for y in range(imy):
                for x in range(imx):
                    # 颜色bitmask
                    w = input[x + y * imx + z * imx * imy]
                    for i in range(c):
                        # 这么做可以包含通配符
                        if w & 1 == 1:
                            # 如果右移i次恢复成1，则说明这个颜色是全局颜色中的第i个颜色，因为bitmask是1左移i次得到的
                            ishifts[i].append((x, y, z))
                        w >>= 1
        self.ishifts = ishifts
        """输入pattern中每种颜色在全局颜色中的空间位置，ishifts[i] 包含 (x, y, z)"""

        if omx == imx and omy == imy and omz == imz:
            oshifts = []
            for i in range(c):
                oshifts.append([])
            for z in range(omz):
                for y in range(omy):
                    for x in range(omx):
                        o = output[x + y * omx + z * omx * omy]
                        if o != 255:
                            oshifts[o].append((x, y, z))
                        else:
                            for i in range(c):
                                oshifts[i].append((x, y, z))
            self.oshifts = oshifts
        wildcard = (1 << c) - 1
        self.binput = []
        for w in input:
            w = 255 if w == wildcard else Rule.first_non_zero_position(w)
            self.binput.append(w)

    def __members(self):
        return (str(self.input), self.imx, self.imy, self.imz, str(self.output), self.omz, self.omy, self.omz)

    # def __eq__(self, other: Rule) -> bool:
    #     return self.__members() == other.__members()

    # def __hash__(self):
    #     return hash(self.__members())

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
        if is_2d:
            return SymmetryHelper.square_symmetries(self, lambda r: r.z_rotated(), lambda r: r.reflected(), __class__.same, symmetry)
        else:
            return SymmetryHelper.cube_symmetries(self, lambda r: r.z_rotated(), lambda r: r.y_rotated(), lambda r: r.reflected(), __class__.same, symmetry)

    @staticmethod
    def same(r1: Rule, r2: Rule) -> bool:
        return r1.__members() == r2.__members()

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
        """
        将原始pattern表达式（包含颜色和空间标识符）解析为颜色字符列表和三维信息
        """
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
                result += gout.folder + "/"
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
            out_rect, omx, omy, omz = Rule.parse(out_str) if out_str is not None else Rule.load_resource(
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
            imx = omx = fx // 2
            imy = omy = fy
            imz = omz = fz
            in_rect = ArrayHelper.flat_array_3d(
                fx // 2, fy, fz, lambda x, y, z: rect[x + y * fx + z * fx * fy])
            out_rect = ArrayHelper.flat_array_3d(
                fx // 2, fy, fz, lambda x, y, z: rect[x + fx // 2 + y * fx + z * fx * fy])
        # 输入图案的颜色bitmask（移位操作生成的，不是0、1、2这种自然索引）
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
        p = float(element.get("p", 1.0))
        return cls(input, imx, imy, imz, output, omx, omy, omz, gin.c, p, in_str, out_str)

    @staticmethod
    def first_non_zero_position(i):
        for p in range(32):
            if (i & 1) == 1:
                return p
            i >>= 1
        return 255


if __name__ == "__main__":
    a = [1, 2]
    print(str(a), a)
