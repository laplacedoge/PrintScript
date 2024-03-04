from abc import ABC, abstractmethod

class Generator(ABC):
    @abstractmethod
    def makeScript(self) -> bytes:
        pass
