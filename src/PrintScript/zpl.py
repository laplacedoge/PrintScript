from . import common, device
import crcmod, zlib, base64
from numba import jit
import numpy as np
import cv2 as cv
import math

@jit(nopython=True, cache=True)
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

class Generator(common.Generator):
    LINE_BREAK = b"\r\n"

    crc16Ccitt = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0xFFFF, xorOut=0x0000)

    def __init__(self) -> None:
        super().__init__()

        self.__resetParam()

    def __resetParam(self):
        self.eol = Generator.LINE_BREAK

        self.printWidth = device.DEFAULT_PRINT_WIDTH
        self.labelLength = device.DEFAULT_LABEL_LENGTH
        self.labelHomePos = device.DEFAULT_LABEL_HOME_POS
        self.labelShift = device.DEFAULT_LABEL_SHIFT

        self.textQueue = []
        self.graphQueue = []

    def clear(self):
        self.__resetParam()

    def setEol(self, eol: str) -> "Generator":
        self.eol = eol
        return self

    def setPrintWidth(self, width: int) -> "Generator":
        self.printWidth = width
        return self

    def setLabelLength(self, length: int) -> "Generator":
        self.labelLength = length
        return self

    def setLabelHomePosition(self, pos: tuple) -> "Generator":
        if isinstance(pos, list):
            pos = tuple(pos)
        self.labelHomePos = pos
        return self

    def setLabelShift(self, shift: int) -> "Generator":
        self.labelShift = shift
        return self

    def __makeZ64Data(self, data: bytes) -> bytes:
        crc16 = Generator.crc16Ccitt(data)
        compressed = zlib.compress(data)
        encoded = base64.b64encode(compressed)

        script = b":Z64:" + encoded + f":{crc16:04X}".encode("ascii")

        return script

    def addGraphicField(self, pos: tuple, size: tuple, path: str) -> "Generator":
        script = bytearray()

        originalImage = cv.imread(path, cv.IMREAD_GRAYSCALE)

        posX = pos[0]
        posY = pos[1]

        originalWidth = originalImage.shape[1]
        originalHeight = originalImage.shape[0]

        desiredWidth = size[0]
        desiredHeight = size[1]

        if desiredWidth == -1:
            resizedWidth = round(originalWidth * (desiredHeight / originalHeight))
            resizedHeight = desiredHeight
        elif desiredHeight == -1:
            resizedWidth = desiredWidth
            resizedHeight = round(originalHeight * (desiredWidth / originalWidth))
        else:
            resizedWidth = desiredWidth
            resizedHeight = desiredHeight

        resizedImage = cv.resize(originalImage, (resizedWidth, resizedHeight), interpolation=cv.INTER_CUBIC)

        imageMaxY = posY + resizedHeight
        imageMaxX = posX + resizedWidth

        croppedWidth = self.printWidth - posX if imageMaxX > self.printWidth else resizedWidth
        croppedHeight = self.labelLength - posY if imageMaxY > self.labelLength else resizedHeight

        croppedImage = resizedImage[:croppedHeight,:croppedWidth]

        paddedWidth = math.ceil(croppedWidth / 8) * 8
        paddingDots = paddedWidth - croppedWidth

        paddedImage = np.pad(croppedImage, ((0, 0), (0, paddingDots)), mode='constant', constant_values=255)

        finalWidth = paddedWidth
        finalHeight = croppedHeight
        finalImage = paddedImage

        finalImage = FloydSteinbergDither(finalImage)

        finalImage = 255 - finalImage

        finalImage = finalImage.reshape((-1, 8))

        finalImage = np.packbits(finalImage, axis=-1)

        data = finalImage.tobytes()

        bytesPerRow = finalWidth // 8

        dataLen = len(data)

        script += f"^FO{pos[0]},{pos[1]}".encode("ascii") + self.eol
        script += f"^GFA,{dataLen},{dataLen},{bytesPerRow},".encode("ascii") + self.__makeZ64Data(data) + self.eol

        self.graphQueue.append(script)

        return self

    def makeScript(self) -> bytes:
        script = bytearray()

        script += b"^XA" + self.eol

        script += f"^PW{self.printWidth}".encode("ascii") + self.eol
        script += f"^LL{self.labelLength}".encode("ascii") + self.eol
        script += f"^LH{self.labelHomePos[0]},{self.labelHomePos[1]}".encode("ascii") + self.eol
        script += f"^LS{self.labelShift}".encode("ascii") + self.eol

        for graph in self.graphQueue:
            script += graph

        script += b"^XZ"

        return bytes(script)
