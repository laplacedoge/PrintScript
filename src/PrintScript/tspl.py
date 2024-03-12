from typing import Tuple, Union
from . import common

class Generator(common.Generator):
    DEF_LINE_BREAK = "\r\n"

    def __init__(self) -> None:
        super().__init__()

        self.__resetParam()

    def __resetParam(self):
        self.eol = Generator.DEF_LINE_BREAK
        self.labelWidth = 0
        self.labelLength = 0
        self.labelSizeUnit = "inch"
        self.labelOffset = 0
        self.labelOffsetUnit = "inch"
        self.printSpeed = 0
        self.printDensity = 0
        self.vFlip = False
        self.hFlip = False
        self.refPosX = 0
        self.refPosY = 0
        self.shiftX = 0
        self.shiftY = 0

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
            unit: str="inch"
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

    def setLabelOffset(self, offset: Union[int, float], unit: str="inch") -> "Generator":
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

    def makeScript(self) -> bytes:
        script = bytearray()

        snippet = ""

        # place SIZE command
        if self.labelSizeUnit == "inch":
            snippet = f"{self.labelWidth}"
            if self.labelLength is not None:
                snippet += f", {self.labelLength}"
        elif self.labelSizeUnit == "mm":
            snippet = f"{self.labelWidth} mm"
            if self.labelLength is not None:
                snippet += f", {self.labelLength} mm"
        elif self.labelSizeUnit == "dot":
            snippet = f"{self.labelWidth} dot"
            if self.labelLength is not None:
                snippet += f", {self.labelLength} dot"
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
        script += f"DIRECTION {1 if self.vFlip else 0}, {1 if self.hFlip else 0}{self.eol}".encode("ascii")

        # place REFERENCE command
        script += f"REFERENCE {self.refPosX}, {self.refPosY}{self.eol}".encode("ascii")

        # place SHIFT command
        script += f"SHIFT {self.shiftX}, {self.shiftY}{self.eol}".encode("ascii")

        return bytes(script)
