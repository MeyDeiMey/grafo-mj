# word_sources/word_source.py

from abc import ABC, abstractmethod
from typing import Dict, Set

class WordSource(ABC):
    @abstractmethod
    def get_words(self) -> Dict[int, Set[str]]:
        """Retorna {longitud: set de palabras}."""
        pass

    @abstractmethod
    def save_raw_data(self, data_lake_path: str) -> None:
        """Guarda la data cruda (e.g. texto original) en data_lake/."""
        pass
