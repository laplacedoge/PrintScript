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
        self.refPosX = 0
        self.refPosY = 0

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

        # place REFERENCE command
        script += f"REFERENCE {self.refPosX}, {self.refPosY}{self.eol}".encode("ascii")

        return bytes(script)
