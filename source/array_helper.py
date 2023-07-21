class ArrayHelper:

    @staticmethod
    def flat_array_3d(mx, my, mz, f):
        return [f(x, y, z) for z in range(mz) for y in range(my) for x in range(mx)]
