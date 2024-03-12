from typing import Tuple, Union
from . import common
import cv2 as cv

class Generator(common.Generator):
    DEF_LINE_BREAK = "\r\n"

    def __init__(self) -> None:
        super().__init__()

        self.__resetParam()

    def __resetParam(self):
        self.eol = Generator.DEF_LINE_BREAK
        self.labelWidth = 0
        self.labelLength = 0
        self.labelSizeUnit = "mm"
        self.labelOffset = 0
        self.labelOffsetUnit = "mm"
        self.printSpeed = 0
        self.printDensity = 0
        self.vFlip = False
        self.hFlip = False
        self.refPosX = 0
        self.refPosY = 0
        self.shiftX = 0
        self.shiftY = 0
        self.clrImgBuf = True

        # specifies how many sets of labels will be printed
        self.setNum = 1

        # specifies how many copies should be
        # printed for each particular label set
        self.cpyNum = 1

        # bitmap queue
        self.bitmapQueue = []

    def clear(self):
        """Reset all the internal parameters and clear all the images.
        """

        self.__resetParam()

    def setEol(self, eol: str) -> "Generator":
        """Set the end-of-line string.

        Parameters:
        eol -- the end-of-line string
        """

        self.eol = eol

        return self

    def setLabelSize(
            self,
            size: Tuple[Union[int, float],
                        Union[int, float]],
            unit: str="mm"
        ) -> "Generator":
        """Set the width and length of the label.

        Parameters:
        size -- the width and length of the label, specified as (x, y)
        unit -- the unit of measurement, it must be inch, mm, or dot
        """

        if not unit in ("inch", "mm", "dot"):
            raise ValueError("The unit of measurement must be inch, mm, or dot")

        if not isinstance(size, tuple) or \
           not all(isinstance(item, (int, float)) for item in size):
            raise TypeError("The size must be a tuple of one or two numbers")

        if not len(size) <= 2:
            raise ValueError("The size must be a tuple of one or two numbers")

        if unit == "dot" and \
           not all(isinstance(item, int) for item in size):
            raise TypeError("The size must be a tuple of integer when " + \
                            "the unit of measurement is dot")

        self.labelWidth = size[0]
        self.labelLength = size[1] if len(size) == 2 else None
        self.labelSizeUnit = unit

        return self

    def setLabelOffset(self, offset: Union[int, float], unit: str="mm") -> "Generator":
        """Set the extra feeding length of the label.

        Parameters:
        offset -- the extra feeding length of the label
        unit -- the unit of measurement, it must be inch, mm, or dot
        """

        if not unit in ("inch", "mm", "dot"):
            raise ValueError("The unit of measurement must be inch, mm, or dot")

        if unit == "inch" or unit == "mm":
            if not isinstance(offset, (int, float)):
                raise TypeError("The offset must be a number when " + \
                                "the unit of measurement is inch or mm")
        elif unit == "dot":
            if not isinstance(offset, int):
                raise TypeError("The offset must be a tuple of integer when " + \
                                "the unit of measurement is dot")

        self.labelOffset = offset
        self.labelOffsetUnit = unit

        return self

    def setPrintSpeed(
            self,
            speed: Union[int, float]
        ) -> "Generator":

        if not isinstance(speed, (int, float)):
            raise TypeError("The speed must be a number")

        self.printSpeed = float(speed) if isinstance(speed, int) else speed

        return self

    def setPrintDensity(
            self,
            density: int
        ) -> "Generator":

        if not isinstance(density, int):
            raise TypeError("The speed must be a integer")

        if density < 0 or \
           density > 15:
            raise ValueError("The speed must be a between 1 and 15")

        self.printDensity = density

        return self

    def setPrintDarkness(
            self,
            darkness: int
        ) -> "Generator":

        return self.setPrintDensity(darkness)

    def setPrintDirection(
            self,
            vFlip: bool,
            hFlip: bool = False
        ) -> "Generator":

        """Set the printout direction and mirror image

        Parameters:
        vFlip -- whether to flip the image vertically
        hFlip -- whether to flip the image horizontally
        """

        if not isinstance(vFlip, bool) or \
           not isinstance(hFlip, bool):
            raise ValueError("The vFlip and hFlip must be of boolean")

        self.vFlip = vFlip
        self.hFlip = hFlip

        return self

    def setReferencePoint(self, pos: tuple) -> "Generator":
        """Set the reference point of the label.

        The reference (origin) point varies with the print direction.

        Parameters:
        pos -- the position of the reference point, specified as (x, y) in dots
        """

        if not isinstance(pos, tuple) or \
           not all(isinstance(item, int) for item in pos):
            raise TypeError("The position must be a tuple of exactly two integers")
        if not len(pos) == 2:
            raise ValueError("The position must be a tuple of exactly two integers")

        self.refPosX = pos[0]
        self.refPosY = pos[1]

        return self

    def setLabelShift(
            self,
            shiftX: int,
            shiftY: int
        ) -> "Generator":

        """Set the printout direction and mirror image

        Parameters:
        shiftX -- X-axis shift (int dots)
        shiftY -- Y-axis shift (int dots)
        """

        if not isinstance(shiftX, bool) or \
           not isinstance(shiftY, bool):
            raise ValueError("The shiftX and shiftY must be integers")

        self.shiftX = shiftX
        self.shiftY = shiftY

        return self

    def setImageBufferClear(
            self,
            cleared: bool
        ) -> "Generator":

        """Set the printout direction and mirror image

        Parameters:
        shiftX -- X-axis shift (int dots)
        shiftY -- Y-axis shift (int dots)
        """

        if not isinstance(cleared, bool):
            raise ValueError("The argument 'cleared' must be of boolean")

        self.clrImgBuf = cleared

        return self

    def setPrintNumber(
            self,
            setNum: int,
            cpyNum: int = 1
        ) -> "Generator":

        """Set the number of print

        Parameters:
        setNum -- the number of sets of labels will be printed
        cpyNum -- the number of copies for each set
        """

        if not isinstance(setNum, int):
            raise TypeError("The argument 'setNum' must be a integer")

        if not isinstance(cpyNum, int):
            raise TypeError("The argument 'cpyNum' must be a integer")

        if setNum < 1 or \
           setNum > 999999999:
            raise ValueError("The argument 'setNum' must be between 1 and 999999999")

        if cpyNum < 1 or \
           cpyNum > 999999999:
            raise ValueError("The argument 'cpyNum' must be between 1 and 999999999")

        self.setNum = setNum
        self.cpyNum = cpyNum

        return self

    def addBitmap(
            self,
            pos: Tuple[int, int],
            size: Tuple[int, int],
            path: str,
            mode: str=""
        ) -> "Generator":

        """Add a bitmap image

        Parameters:
        pos -- expected image position
        size -- expected image size
        path -- the path of the image
        mode -- graphic mode, must be 'overwrite', 'or', or 'xor'
        """

        import os, math
        import numpy as np
        from .algorithm import FloydSteinbergDither

        if not isinstance(pos, tuple) or \
           not all(isinstance(item, int) for item in pos):
            raise TypeError("The argument 'pos' must be a tuple of exactly two integers")

        if not isinstance(size, tuple) or \
           not all(isinstance(item, int) for item in size):
            raise TypeError("The argument 'size' must be a tuple of exactly two integers")

        if not isinstance(mode, str):
            raise TypeError("The argument 'mode' must be a string")

        posX, posY = pos
        if posX < 0 or \
           posY < 0:
            raise ValueError("The integer in the argument 'pos' must be a positive")

        desiredWidth, desiredHeight = size
        if desiredWidth == -1 and \
           desiredHeight == -1:
            raise ValueError("The image width and height cannot be -1 at the same time")

        mode = mode.lower()
        if not mode == "overwrite" and \
           not mode == "or" and \
           not mode == "xor":
            raise ValueError("The argument 'mode' must be 'overwrite', 'or', or 'xor'")

        if not os.path.isfile(path):
            raise FileNotFoundError(f"file '{path}' is not found")

        originalImage: np.ndarray = cv.imread(path, cv.IMREAD_GRAYSCALE)
        if originalImage is None:
            raise ValueError(f"file '{path}' is not a valid image")

        originalHeight, originalWidth = originalImage.shape

        # resize image
        if desiredHeight == -1:
            desiredHeight = round(desiredWidth / originalWidth * originalHeight)
        elif desiredWidth == -1:
            desiredWidth = round(desiredHeight / originalHeight * originalWidth)
        desiredImage = cv.resize(originalImage, (desiredWidth, desiredHeight),
                                 interpolation=cv.INTER_CUBIC)

        # pad image
        paddedWidth = math.ceil(desiredWidth / 8) * 8
        paddedHeight = desiredHeight
        paddingPixels = paddedWidth - desiredWidth
        paddedImage = np.pad(desiredImage, ((0, 0), (0, paddingPixels)),
                             mode='constant', constant_values=255)

        # dither image
        ditheredImage = FloydSteinbergDither(paddedImage)
        ditheredWidth = paddedWidth
        ditheredHeight = paddedHeight

        # pack image
        packedImage = np.packbits(ditheredImage, axis=-1)

        # image width (int bytes)
        imageWidth = ditheredWidth // 8

        imageHeight = ditheredHeight

        if mode == "overwrite":
            modeIndicator = 0
        if mode == "or":
            modeIndicator = 1
        if mode == "xor":
            modeIndicator = 2
        else:
            modeIndicator = 0

        imageData = packedImage.tobytes()

        script = bytearray()
        script += f"BITMAP {posX},{posY},{imageWidth},{ditheredHeight},{modeIndicator},".encode("ascii")
        script += imageData
        script += self.eol.encode("ascii")

        self.bitmapQueue.append(script)

        return self

    def makeScript(self) -> bytes:
        script = bytearray()

        snippet = ""

        # place SIZE command
        if self.labelSizeUnit == "inch":
            snippet = f"{self.labelWidth}"
            if self.labelLength is not None:
                snippet += f",{self.labelLength}"
        elif self.labelSizeUnit == "mm":
            snippet = f"{self.labelWidth} mm"
            if self.labelLength is not None:
                snippet += f",{self.labelLength} mm"
        elif self.labelSizeUnit == "dot":
            snippet = f"{self.labelWidth} dot"
            if self.labelLength is not None:
                snippet += f",{self.labelLength} dot"
        script += f"SIZE {snippet}{self.eol}".encode("ascii")

        # place OFFSET command
        if self.labelOffsetUnit == "inch":
            snippet = f"{self.labelOffset}"
        elif self.labelOffsetUnit == "mm":
            snippet = f"{self.labelOffset} mm"
        elif self.labelOffsetUnit == "dot":
            snippet = f"{self.labelOffset} dot"
        script += f"OFFSET {snippet}{self.eol}".encode("ascii")

        # place SPEED command
        script += f"SPEED {self.printSpeed}{self.eol}".encode("ascii")

        # place DENSITY command
        script += f"DENSITY {self.printDensity}{self.eol}".encode("ascii")

        # place DIRECTION command
        script += f"DIRECTION {1 if self.vFlip else 0},{1 if self.hFlip else 0}{self.eol}".encode("ascii")

        # place REFERENCE command
        script += f"REFERENCE {self.refPosX},{self.refPosY}{self.eol}".encode("ascii")

        # place SHIFT command
        script += f"SHIFT {self.shiftX},{self.shiftY}{self.eol}".encode("ascii")

        # place SHIFT command
        if self.clrImgBuf:
            script += f"CLS{self.eol}".encode("ascii")

        # place BITMAP command
        for bitmap in self.bitmapQueue:
            script += bitmap

        # place PRINT command
        script += f"PRINT {self.setNum},{self.cpyNum}{self.eol}".encode("ascii")

        return bytes(script)
