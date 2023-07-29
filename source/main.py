import os
import sys
import time
import random
import shutil
import traceback
import numpy as np
import matplotlib.pyplot as plt
from voxio import write_list_to_vox
from PIL import Image
from lxml import etree
from lxml.etree import _Element
from interpreter import Interpreter


def hex_to_rgb(hex_color):
    hex_color = hex_color.strip("#")
    rgb_tuple = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    return rgb_tuple


def delete_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def flat_index_to_2d_index(flat_index, num_cols):
    row_index = flat_index // num_cols
    col_index = flat_index % num_cols
    return row_index, col_index


if __name__ == "__main__":
    start = time.time()
    output_path = "output"
    delete_files(output_path)
    palette = {x.get("symbol"): hex_to_rgb(x.get("value")) for x in etree.parse(
        f"resources/palette.xml").getroot().findall("color")}
    models: list[_Element] = etree.parse(
        f"models.xml").getroot().findall("model")
    for i, model in enumerate(models):
        name = model.get("name")
        linear_size = model.get("size", -1)
        dimension = model.get("d", 2)
        mx = int(model.get("length", linear_size))
        my = int(model.get("width", linear_size))
        mz = int(model.get("height", 1 if dimension == 2 else linear_size))
        print(f"{name} > ")
        file_name = f"models/{name}.xml"
        try:
            interpreter = Interpreter(file_name, mx, my, mz)
        except Exception as e:
            traceback.print_exc()
            break
            # continue

        amount = int(model.get("amount", 1))
        amount = 4
        pixel_size = int(model.get("pixelsize", 4))
        seeds_str = model.get("seeds")
        seeds = [] if seeds_str is None else list(map(int, seeds.split()))
        gif = bool(model.get("gif", False))
        if gif:
            amount = 1
        iso = model.get("iso", False)
        steps = int(model.get("steps", 1000 if gif else 50000))
        gui = int(model.get("gui", 0))
        custom_palette = dict(palette)
        for c in model.findall("color"):
            custom_palette[c.get("symbol")] = hex_to_rgb(c.get("value"))
        if mz == 1:
            fig, axes = plt.subplots(nrows=1, ncols=(
                amount), num=name, subplot_kw={"projection": "3d"})
        else:
            row = 2
            col = amount // row
            fig, axes = plt.subplots(
                nrows=row, ncols=col, num=name, subplot_kw={"projection": "3d"})
            print("len(axes)", len(axes))
            fig.set_size_inches(12, 7)
            # fig = plt.figure()
            # axe = fig.add_subplot(projection="3d")
        for k in range(amount):
            seed = seeds[k] if seeds and k < len(
                seeds) else random.randint(0, sys.maxsize)
            for result, legend, fx, fy, fz in interpreter.run(seed, steps, gif):
                colors = [custom_palette[c] for c in legend]
                result = np.take(colors, result, axis=0)
                if mz == 1:
                    image = np.reshape(result, (fx, fy, 3))
                    new_image = Image.fromarray(np.uint8(image))
                    new_image.save(f"{output_path}/{interpreter.counter}.png")
                    a = axes[k] if isinstance(axes, np.ndarray) else axes
                    a.imshow(image)
                else:
                    image = np.reshape(result, (fx, fy, fz, 3))
                    u = np.transpose(image, axes=(2, 1, 0, 3))
                    axes[flat_index_to_2d_index(k, col)].voxels((u[:, :, :, 2] > 0.1),
                                                                facecolors=np.clip(u[:, :, :, :4], 0, 1))
                    fig.canvas.draw()
                plt.pause(0.01)
    print(f"Execute Time: {round(time.time() - start, 2)} s")
    plt.show()
