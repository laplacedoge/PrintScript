from abc import ABC, abstractmethod

class Generator(ABC):
    @abstractmethod
    def generateScript(self) -> bytes:
        pass
