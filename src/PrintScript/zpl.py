from . import common, device
import crcmod, zlib, base64
import cv2 as cv
import numpy as np
import math

class ZplGenerator(common.Generator):
    LINE_BREAK = b"\r\n"

    crc16Ccitt = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0xFFFF, xorOut=0x0000)

    def __init__(self) -> None:
        super().__init__()

        self.eol = ZplGenerator.LINE_BREAK

        self.printWidth = device.DEFAULT_PRINT_WIDTH
        self.labelLength = device.DEFAULT_LABEL_LENGTH
        self.labelHomePos = device.DEFAULT_LABEL_HOME_POS
        self.labelShift = device.DEFAULT_LABEL_SHIFT

        self.graphList = []

    def setEol(self, eol: str):
        self.eol = eol

    def setPrintWidth(self, width: int) -> "ZplGenerator":
        self.printWidth = width

    def setLabelLength(self, length: int) -> "ZplGenerator":
        self.labelLength = length

    def setLabelHomePosition(self, pos: tuple | list) -> "ZplGenerator":
        if isinstance(pos, list):
            pos = tuple(pos)

        self.labelHomePos = pos

    def setLabelShift(self, shift: int) -> "ZplGenerator":
        self.labelShift = shift

    def __MakeZ64Data(self, data: bytes) -> bytes:
        crc16 = ZplGenerator.crc16Ccitt(data)
        compressed = zlib.compress(data)
        encoded = base64.b64encode(compressed)

        srcBytes = len(data)
        compBytes = len(compressed)
        encBytes = len(encoded)

        print("Compression rate: {:.2f}/{:.2f} KiB ({:.2f}%)".format(
            compBytes / 1024, srcBytes / 1024, compBytes / srcBytes * 100))
        print("Decrease rate: {:.2f}/{:.2f} KiB ({:.2f}%)".format(
            encBytes / 1024, srcBytes / 1024, encBytes / srcBytes * 100))

        script = b":Z64:" + encoded + f":{crc16:04X}".encode("ascii")

        return script

    def get_new_val(self, old_val, nc):
        """
        Get the "closest" colour to old_val in the range [0,1] per channel divided
        into nc values.

        """

        return np.round(old_val * (nc - 1)) / (nc - 1)

    def floydSteinbergDither(self, img, nc):
        """
        Floyd-Steinberg dither the image img into a palette with nc colours per
        channel.

        """

        arr = np.array(img, dtype=float) / 255

        new_height = arr.shape[0]
        new_width = arr.shape[1]

        for ir in range(new_height):
            for ic in range(new_width):
                # NB need to copy here for RGB arrays otherwise err will be (0,0,0)!
                old_val = arr[ir, ic].copy()
                new_val = self.get_new_val(old_val, nc)
                arr[ir, ic] = new_val
                err = old_val - new_val
                # In this simple example, we will just ignore the border pixels.
                if ic < new_width - 1:
                    arr[ir, ic+1] += err * 7/16
                if ir < new_height - 1:
                    if ic > 0:
                        arr[ir+1, ic-1] += err * 3/16
                    arr[ir+1, ic] += err * 5/16
                    if ic < new_width - 1:
                        arr[ir+1, ic+1] += err / 16

        carr = np.array(arr/np.max(arr, axis=(0,1)) * 255, dtype=np.uint8)

        return carr

    def addGraphicField(self, pos: tuple | list, size: tuple | list, path: str, comp: str="") -> "ZplGenerator":
        script = bytearray()

        originalImage = cv.imread(path, cv.IMREAD_GRAYSCALE)

        posX = pos[0]
        posY = pos[1]

        originalWidth = originalImage.shape[1]
        originalHeight = originalImage.shape[0]

        print(f"originalSize: {originalWidth},{originalHeight}")

        desiredWidth = size[0]
        desiredHeight = size[1]

        print(f"desiredSize: {desiredWidth},{desiredHeight}")

        if desiredWidth == -1:
            resizedWidth = round(originalWidth * (desiredHeight / originalHeight))
            resizedHeight = desiredHeight
        elif desiredHeight == -1:
            resizedWidth = desiredWidth
            resizedHeight = round(originalHeight * (desiredWidth / originalWidth))
        else:
            resizedWidth = desiredWidth
            resizedHeight = desiredHeight

        print(f"resizedSize: {resizedWidth},{resizedHeight}")

        resizedImage = cv.resize(originalImage, (resizedWidth, resizedHeight), interpolation=cv.INTER_CUBIC)

        cv.imwrite(path + ".resized.png", resizedImage)

        imageMaxY = posY + resizedHeight
        imageMaxX = posX + resizedWidth

        croppedWidth = self.printWidth - posX if imageMaxX > self.printWidth else resizedWidth
        croppedHeight = self.labelLength - posY if imageMaxY > self.labelLength else resizedHeight

        print(f"croppedSize: {croppedWidth},{croppedHeight}")

        croppedImage = resizedImage[:croppedHeight,:croppedWidth]

        paddedWidth = math.ceil(croppedWidth / 8) * 8
        paddingDots = paddedWidth - croppedWidth

        paddedImage = np.pad(croppedImage, ((0, 0), (0, paddingDots)), mode='constant', constant_values=255)

        finalWidth = paddedWidth
        finalHeight = croppedHeight
        finalImage = paddedImage

        print(f"finalSize: {finalWidth},{finalHeight}")

        finalImage = self.floydSteinbergDither(finalImage, 2)

        cv.imwrite(path + ".modified.png", finalImage)

        finalImage = 255 - finalImage

        finalImage = finalImage.reshape((-1, 8))

        finalImage = np.packbits(finalImage, axis=-1)

        data = finalImage.tobytes()

        bytesPerRow = finalWidth // 8

        dataLen = len(data)

        script += f"^FO{pos[0]},{pos[1]}".encode("ascii") + self.eol
        script += f"^GFA,{dataLen},{dataLen},{bytesPerRow},".encode("ascii") + self.__MakeZ64Data(data) + self.eol

        self.graphList.append(script)

    def generateScript(self) -> bytes:
        script = bytearray()

        script += b"^XA" + self.eol

        script += f"^PW{self.printWidth}".encode("ascii") + self.eol
        script += f"^LL{self.labelLength}".encode("ascii") + self.eol
        script += f"^LH{self.labelHomePos[0]},{self.labelHomePos[1]}".encode("ascii") + self.eol
        script += f"^LS{self.labelShift}".encode("ascii") + self.eol

        for graph in self.graphList:
            script += graph

        script += b"^XZ"

        return bytes(script)
