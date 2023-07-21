import random
import numpy as np
import traceback
import matplotlib.pyplot as plt
from lxml import etree
from lxml.etree import _Element
from interpreter import Interpreter
from graphic import Graphic

if __name__ == "__main__":
    palette = {x.get("symbol"): int(x.get("value"), 16) for x in etree.parse(
        f"resources/palette.xml").getroot().findall("color")}
    pass
    models: list[_Element] = etree.parse(
        f"models.xml").getroot().findall("model")
    for model in models:
        name = model.get("name")
        linear_size = model.get("size", -1)
        dimension = model.get("d", 2)
        mx = int(model.get("length", linear_size))
        my = int(model.get("width", linear_size))
        mz = int(model.get("height", 1 if dimension == 2 else linear_size))
        print(f"{name} > ", end="")
        file_name = f"models/{name}.xml"
        try:
            interpreter = Interpreter(file_name, mx, my, mz)
        except Exception as e:
            traceback.print_exc()
            break
            # continue
        amount = model.get("amount", 2)
        pixel_size = model.get("pixelsize", 4)
        seeds_str = model.get("seeds")
        seeds = [] if seeds_str is None else list(map(int, seeds.split()))
        gif = model.get("gif", False)
        if gif:
            amount = 1
        iso = model.get("iso", False)
        steps = int(model.get("steps", 1000 if gif else 50000))
        gui = model.get("gui", 0)
        custom_palette = dict(palette)
        for c in model.findall("color"):
            custom_palette[c.get("symbol")] = int(c.get("value"), 16)
        for k in range(amount):
            seed = seeds[k] if seeds and k < len(
                seeds) else random.randint(0, 2 ** 32 - 1)
            random.seed(seed)
            fig, ax = plt.subplots()
            for result, legend, fx, fy, fz in interpreter.run(steps, gif):
                image = np.reshape(result, (fx, fy))
                im = plt.imshow(image)
                fig.canvas.draw()
                plt.pause(0.001)

                # colors = [custom_palette[ch] for ch in legend]
                # output_name = f"output/{interpreter.counter}" if gif else f"output/{name}_{seed}"
                # if fz == 1 or iso:
                #     bitmap, width, height = Graphic.render(
                #         result, fx, fy, fz, colors, pixel_size, gui)
            print("Done")
    plt.show()
