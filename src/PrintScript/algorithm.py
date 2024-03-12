import numpy as np
import numba as nb

@nb.jit(nopython=True, cache=True)
def FloydSteinbergDither(img: np.ndarray):
    arr = img.astype(np.int32)
    new_height, new_width = arr.shape

    for ir in range(new_height):
        for ic in range(new_width):
            old_val = arr[ir, ic]
            new_val = 0 if old_val < 128 else 255
            arr[ir, ic] = new_val
            err = old_val - new_val

            if ic < new_width - 1:
                arr[ir, ic + 1] += err * 7 // 16
            if ir < new_height - 1:
                if ic > 0:
                    arr[ir + 1, ic - 1] += err * 3 // 16
                arr[ir + 1, ic] += err * 5 // 16
                if ic < new_width - 1:
                    arr[ir + 1, ic + 1] += err // 16

    np.clip(arr, 0, 255, out=arr)

    return arr.astype(np.uint8)
