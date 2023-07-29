from __future__ import annotations
import time
import numpy as np
from random import Random
from lxml import etree
from grid import Grid
from wfc_node import WFCNode
from helper import Helper
from graphic import Graphic
from symmetry_helper import SymmetryHelper
from vox_helper import VoxHelper
from array_helper import ArrayHelper
from helper import Helper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lxml.etree import _Element


class TileNode(WFCNode):

    def __init__(self) -> None:
        super().__init__()

    def load(self, element: _Element, parent_symmetry: list[bool], grid: Grid) -> bool:
        print("TileNode load")
        self.periodic = bool(element.get("periodic", False))
        self.name = element.get("tileset")
        self.overlap = int(element.get("overlap", 0))
        self.overlapz = int(element.get("overlapz", 0))
        file_path = f"resources/tilesets/{self.name}.xml"
        root: _Element = etree.parse(file_path).getroot()
        full_symmetry = bool(root.get("fullSymmetry", False))
        first_tile = root.find("tiles").find("tile")
        tiles_name = element.get("tiles", self.name)
        first_file_name = f"{tiles_name}/{first_tile.get('name')}.vox"
        first_data, self.S, SY, self.SZ = VoxHelper.load_vox(
            f"resources/tilesets/{first_file_name}")
        if first_data is None:
            print(f"couldn't read {first_file_name}")
            return False
        if self.S != SY:
            print(f"tiles should be square shaped: {self.S} != {SY}")
            return False
        if full_symmetry and self.S != self.SZ:
            print(
                f"tiles should be cubes for the full symmetry option: {self.S} != {self.SZ}")
            return False
        self.new_grid = Grid(element, (self.S - self.overlap) * grid.mx + self.overlap, (self.S - self.overlap)
                             * grid.my + self.overlap, (self.SZ - self.overlap) * grid.mz + self.overlap)
        if self.new_grid is None:
            return False

        def new_tile(f):
            return ArrayHelper.flat_array_3d(self.S, self.S, self.SZ, f)

        def z_rotate(p):
            return new_tile(lambda x, y, z: p[y + (self.S - 1 - x) * self.S + z * self.S ** 2])

        def y_rotate(p):
            return new_tile(lambda x, y, z: p[z + y * self.S + (self.S - 1 - x) * self.S ** 2])

        def x_rotate(p):
            return new_tile(lambda x, y, z: p[x + z * self.S + (self.S - 1 - y) * self.S ** 2])

        def x_reflect(p):
            return new_tile(lambda x, y, z: p[(self.S - 1 - x) + y * self.S + z * self.S ** 2])

        def y_reflect(p):
            return new_tile(lambda x, y, z: p[x + (self.S - 1 - y) * self.S + z * self.S ** 2])

        def z_reflect(p):
            return new_tile(lambda x, y, z: p[x + y * self.S + (self.S - 1 - z) * self.S ** 2])

        self.tile_data = []
        named_tile_data = {}
        temp_stationary = []
        positions = {}
        uniques = []
        tiles: list[_Element] = root.find("tiles").findall("tile")
        ind = 0
        for tile in tiles:
            tile_name = tile.get("name")
            weight = float(tile.get("weight", 1.0))
            file_name = f"resources/tilesets/{tiles_name}/{tile_name}.vox"
            vox = VoxHelper.load_vox(file_name)[0]
            if vox is None:
                print(f"couldn't read tile {file_name}")
                return False
            flat_tile, C = Helper.ords(vox, uniques)
            if C > self.new_grid.c:
                print(
                    f"there were more than {self.new_grid.c} colors in vox files")
                return False
            local_data = SymmetryHelper.cube_symmetries(flat_tile, z_rotate, y_rotate, x_reflect, lambda q1, q2: q1 ==
                                                        q2) if full_symmetry else SymmetryHelper.square_symmetries(flat_tile, z_rotate, x_reflect, lambda q1, q2: q1 == q2)

            named_tile_data[tile_name] = local_data
            position = [False] * 128
            for p in local_data:
                self.tile_data.append(p)
                temp_stationary.append(weight)
                position[ind] = True
                ind += 1
            positions[tile_name] = position
        self.P = len(self.tile_data)
        print(f"P = {self.P}")
        self.weights = temp_stationary
        for rule in element.findall("rule"):
            input = rule.get("in")
            outputs = rule.get("out").split("|")
            position = [False] * self.P
            for s in outputs:
                if s not in positions:
                    print(f"unknown tilename {s} at line {rule.sourceline}")
                    return False
                array = positions[s]
                for p in range(self.P):
                    if array[p]:
                        position[p] = True
            self.map[grid.values[input]] = position
        if 0 not in self.map:
            self.map[0] = [True] * self.P
        temp_propagator = np.full((6, self.P, self.P), False)

        def index(p):
            for i, v in enumerate(self.tile_data):
                if p == v:
                    return i
            return -1

        def last(attribute: str):
            return attribute.split()[-1]

        def tile(attribute):
            code = attribute.split()
            action = code[0] if len(code) == 2 else ""
            start_tile = named_tile_data[last(attribute)][0]
            for i in range(len(action) - 1, -1, -1):
                sym = action[i]
                if sym == "x":
                    start_tile = x_rotate(start_tile)
                elif sym == "y":
                    start_tile = y_rotate(start_tile)
                elif sym == "z":
                    start_tile = z_rotate(start_tile)
                else:
                    print(f"unknown symmetry {sym}")
                    return None
            return start_tile

        tile_names = [tile.get("name") for tile in tiles]
        tile_names.append(None)
        neighbors: list[_Element] = root.find("neighbors").findall("neighbor")
        for neighbor in neighbors:
            if full_symmetry:
                left, right = neighbor.get("left"), neighbor.get("right")
                if last(left) not in tile_names or last(right) not in tile_names:
                    print(
                        f"unknown tile {last(left)} or {last(right)} at line {neighbor.sourceline}")
                    return False
                ltile, rtile = tile(left), tile(right)
                if ltile is None or rtile is None:
                    return False
                lsym = SymmetryHelper.square_symmetries(
                    ltile, x_rotate, y_reflect, lambda q1, q2: False)
                rsym = SymmetryHelper.square_symmetries(
                    rtile, x_rotate, y_reflect, lambda q1, q2: False)
                for i, v in enumerate(lsym):
                    temp_propagator[0, index(v), index(rsym[i])] = True
                    temp_propagator[0, index(
                        x_reflect(rsym[i])), index(x_reflect(v))] = True
                dtile, utile = z_rotate(ltile), z_rotate(rtile)
                dsym = SymmetryHelper.square_symmetries(
                    dtile, y_rotate, z_reflect, lambda q1, q2: False)
                usym = SymmetryHelper.square_symmetries(
                    utile, y_rotate, z_reflect, lambda q1, q2: False)
                for i, v in enumerate(dsym):
                    temp_propagator[1, index(v), index(usym[i])] = True
                    temp_propagator[1, index(
                        y_reflect(usym[i])), index(y_reflect(v))] = True
                btile, ttile = y_rotate(ltile), y_rotate(rtile)
                bsym = SymmetryHelper.square_symmetries(
                    btile, z_rotate, x_reflect, lambda q1, q2: False)
                tsym = SymmetryHelper.square_symmetries(
                    ttile, z_rotate, x_reflect, lambda q1, q2: False)
                for i, v in enumerate(bsym):
                    temp_propagator[4, index(v), index(tsym[i])] = True
                    temp_propagator[4, index(
                        z_reflect(tsym[i])), index(z_reflect(v))] = True
            elif neighbor.get("left") is not None:
                left, right = neighbor.get("left"), neighbor.get("right")
                if last(left) not in tile_names or last(right) not in tile_names:
                    print(
                        f"unknown tile {last(left)} or {last(right)} at line {neighbor.sourceline}")
                    return False
                ltile, rtile = tile(left), tile(right)
                if ltile is None or rtile is None:
                    return False
                temp_propagator[0, index(ltile), index(rtile)] = True
                temp_propagator[0, index(y_reflect(ltile)), index(
                    y_reflect(rtile))] = True
                temp_propagator[0, index(x_reflect(rtile)), index(
                    x_reflect(ltile))] = True
                temp_propagator[0, index(y_reflect(x_reflect(rtile))), index(
                    y_reflect(x_reflect(ltile)))] = True
                dtile, utile = z_rotate(ltile), z_rotate(rtile)
                temp_propagator[1, index(dtile), index(utile)] = True
                temp_propagator[1, index(x_reflect(dtile)), index(
                    x_reflect(utile))] = True
                temp_propagator[1, index(y_reflect(utile)), index(
                    y_reflect(dtile))] = True
                temp_propagator[1, index(x_reflect(y_reflect(utile))), index(
                    x_reflect(y_reflect(dtile)))] = True
            else:
                top, bottom = neighbor.get("top"), neighbor.get("bottom")
                if last(top) not in tile_names or last(bottom) not in tile_names:
                    print(
                        f"unknown tile {last(top)} or {last(bottom)} at line {neighbor.sourceline}")
                    return False
                ttile, btile = tile(top), tile(bottom)
                if ttile is None or bottom is None:
                    return False
                tsym = SymmetryHelper.square_symmetries(
                    ttile, z_rotate, x_reflect, lambda q1, q2: False)
                bsym = SymmetryHelper.square_symmetries(
                    btile, z_rotate, x_reflect, lambda q1, q2: False)
                for i, v in enumerate(tsym):
                    temp_propagator[4, index(bsym[i]), index(v)] = True
        # for a in temp_propagator:
        #     for b in a:
        #         print("temp_propagator", b.tolist())
        for p2 in range(self.P):
            for p1 in range(self.P):
                temp_propagator[2, p2, p1] = temp_propagator[0, p1, p2]
                temp_propagator[3, p2, p1] = temp_propagator[1, p1, p2]
                temp_propagator[5, p2, p1] = temp_propagator[4, p1, p2]
        sparse_propagator = [None] * 6
        for d in range(6):
            sparse_propagator[d] = [None] * self.P
            for t in range(self.P):
                sparse_propagator[d][t] = []
        self.propagator = [None] * 6
        for d in range(6):
            self.propagator[d] = [None] * self.P
            for p1 in range(self.P):
                sp = sparse_propagator[d][p1]
                tp = temp_propagator[d, p1]
                for p2 in range(self.P):
                    if tp[p2]:
                        sp.append(p2)
                ST = len(sp)
                self.propagator[d][p1] = [0] * ST
                for st in range(ST):
                    self.propagator[d][p1][st] = sp[st]
        return super().load(element, parent_symmetry, grid)

    def update_state(self):
        r = Random()
        for z in range(self.grid.mz):
            for y in range(self.grid.my):
                for x in range(self.grid.mx):
                    w = self.wave.data[x + y * self.grid.mx +
                                       z * self.grid.mx * self.grid.my]
                    votes = np.full(
                        (self.SZ * self.S ** 2, self.new_grid.c), 0)
                    for t in range(self.P):
                        if w[t]:
                            tile = self.tile_data[t]
                            for dz in range(self.SZ):
                                for dy in range(self.S):
                                    for dx in range(self.S):
                                        di = dx + dy * self.S + dz * self.S ** 2
                                        votes[di, tile[di]] += 1
                    for dz in range(self.SZ):
                        for dy in range(self.S):
                            for dx in range(self.S):
                                v = votes[dx + dy * self.S + dz * self.S ** 2]
                                max = -1.0
                                argmax = 255
                                for c, vc in enumerate(v):
                                    vote = vc + 0.1 * r.random()
                                    if vote > max:
                                        argmax = c
                                        max = vote
                                sx = x * (self.S - self.overlap) + dx
                                sy = y * (self.S - self.overlap) + dy
                                sz = z * (self.SZ - self.overlap) + dz
                                self.new_grid.state[sx + sy * self.new_grid.mx +
                                                    sz * self.new_grid.mx * self.new_grid.my] = argmax


if __name__ == "__main__":
    pass
