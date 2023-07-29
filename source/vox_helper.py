from voxio import vox_to_arr


class VoxHelper:

    @staticmethod
    def load_vox(file_name):
        # result = vox_to_arr(file_name)
        # result = result.astype(int)
        # mx, my, mz = result.shape[:3]
        # # return result.flatten(), mx, my, mz
        # return result, mx, my, mz
        return vox_to_arr(file_name)


if __name__ == "__main__":
    import numpy as np
    vox = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 26, 42, 42, 42, 26, 22, 22, 22, 22, 22, 22, 22,
           22, 22, 22, 22, 22, 22, 22, 22, 26, 42, 42, 42, 26, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    vox = np.reshape(vox, (5, 5, 5))
    print(vox)
    a, x, y, z = VoxHelper.load_vox(
        "resources/tilesets/Paths/Line.vox")
    print(a, x, y, z)
