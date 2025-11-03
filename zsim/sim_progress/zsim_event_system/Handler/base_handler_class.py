from abc import ABC, abstractmethod
from collections import defaultdict


class ZSimEventHandler(ABC):
    @abstractmethod
    def handle(self, event):
        pass


