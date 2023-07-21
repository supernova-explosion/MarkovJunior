from midvoxio.voxio import vox_to_arr


class VoxHelper:

    @staticmethod
    def load_vox(file_name):
        result = vox_to_arr(file_name)
        mx, my, mz = result.shape[:3]
        return result, mx, my, mz


if __name__ == "__main__":
    a, x, y, z = VoxHelper.load_vox("resources/test/teapot.vox")
    print(x, y, z)
