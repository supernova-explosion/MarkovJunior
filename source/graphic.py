import numpy as np
from PIL import Image


class Graphic:

    BACKGROUND = "222222"

    @staticmethod
    def load_bitmap(file_name):
        bitmap = Image.open(file_name)
        width = bitmap.width
        height = bitmap.height
        bitmap = bitmap.convert("RGBA")
        pixel_data = bitmap.load()
        result = []
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixel_data[x, y]
                color = r << 16 | g << 8 | b | a << 24
                result.append(color)
        return result, width, height, 1

    @staticmethod
    def render(state, mx, my, mz, colors, pixel_size, margin):
        if mz == 1:
            return Graphic.bitmap_render(state, mx, my, colors, pixel_size, margin)

    @staticmethod
    def bitmap_render(state, mx, my, colors, pixel_size, margin):
        width = mx * pixel_size + margin
        height = my * pixel_size
        total_width = width
        total_height = height
        bitmap = np.full(total_width * total_height, 2)
        # dx = (total_width - width) / 2
        # dy = (total_height - height) / 2
        for y in range(my):
            for x in range(mx):
                c = colors[state[x + y * mx]]
                for dy in range(pixel_size):
                    for dx in range(pixel_size):
                        sx = dx + x * pixel_size
                        sy = dy + y * pixel_size
                        if sx < 0 or sx >= width - margin or sy < 0 or sy >= height:
                            continue
                        bitmap[margin + sx + sy * width] = c
        return bitmap, width, height


if __name__ == "__main__":
    # print(Graphic.render(1, 1, 1, 1, 1, 1, 1))
    data, x, y, z = Graphic.load_bitmap("resources/fonts/Tamzen8x16r.png")
    print(data)
