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
        self.refPosX = 0
        self.refPosY = 0

    def setEol(self, eol: str) -> "Generator":
        """Set the end-of-line string.

        Parameters:
        eol -- the end-of-line string
        """

        self.eol = eol

        return self

    def setLabelSize(self, size: tuple, unit: str="inch") -> "Generator":
        """Set the width and length of the label.

        Parameters:
        size -- the width and length of the label, specified as (x, y)
        unit -- the unit of measurement, it must be inch, mm, or dot
        """

        if not isinstance(size, tuple) or \
           not all(isinstance(item, (int, float)) for item in size):
            raise TypeError("The size must be a tuple of one or two numbers")
        if not len(size) <= 2:
            raise ValueError("The size must be a tuple of one or two numbers")
        if not unit in ("inch", "mm", "dot"):
            raise ValueError("The unit of measurement must be inch, mm, or dot")
        if unit in ("mm", "dot") and \
           not all(isinstance(item, int) for item in size):
            raise TypeError("The size must be a tuple of integer when " + \
                            "the unit of measurement is mm or dot")

        self.labelWidth = size[0]
        self.labelLength = size[1] if len(size) == 2 else None
        self.labelSizeUnit = unit

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

        # place REFERENCE command
        script += f"REFERENCE {self.refPosX}, {self.refPosY}{self.eol}".encode("ascii")

        return bytes(script)
