# word_sources/local_dictionary_word_source.py

import os
import shutil
from typing import Dict, Set
from .word_source import WordSource
from .exceptions import WordSourceException

class LocalDictionaryWordSource(WordSource):
    def __init__(self, file_path: str):
        if not os.path.isfile(file_path):
            raise ValueError(f"Archivo inexistente: {file_path}")
        self.file_path = file_path

    def get_words(self) -> Dict[int, Set[str]]:
        words_by_length = {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip().lower()
                    if self._is_valid_word(w):
                        l = len(w)
                        words_by_length.setdefault(l, set()).add(w)
            return words_by_length
        except OSError as e:
            raise WordSourceException(f"Error leyendo archivo {self.file_path}: {e}")

    def save_raw_data(self, data_lake_path: str) -> None:
        try:
            if not os.path.isdir(data_lake_path):
                os.makedirs(data_lake_path)
            dest = os.path.join(data_lake_path, os.path.basename(self.file_path))
            shutil.copy(self.file_path, dest)
        except OSError as e:
            raise WordSourceException(f"Error guardando archivo en datalake: {e}")

    def _is_valid_word(self, word: str) -> bool:
        return word.isalpha() and len(word) > 0
