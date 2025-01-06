# word_sources/project_gutenberg_word_source.py

import os
import re
import requests
from typing import Dict, Set
from .word_source import WordSource
from .exceptions import WordSourceException

class ProjectGutenbergWordSource(WordSource):
    def __init__(self, book_url: str):
        if not book_url:
            raise ValueError("La URL no puede estar vacía.")
        self.book_url = book_url
        self.raw_content = ""
        self.book_id = self._extract_book_id()

    def get_words(self) -> Dict[int, Set[str]]:
        self._download_book()
        all_words = re.findall(r"\b[a-zA-Z]+\b", self.raw_content)
        words_by_length = {}
        for w in all_words:
            w_lower = w.lower()
            if len(w_lower) >= 3:  # Ej: ignorar <3 letras
                words_by_length.setdefault(len(w_lower), set()).add(w_lower)
        return words_by_length

    def save_raw_data(self, data_lake_path: str) -> None:
        if not os.path.isdir(data_lake_path):
            os.makedirs(data_lake_path)
        file_name = f"gutenberg_{self.book_id}.txt"
        file_path = os.path.join(data_lake_path, file_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.raw_content)
        except OSError as e:
            raise WordSourceException(f"Error guardando en datalake: {e}")

    def _download_book(self):
        try:
            resp = requests.get(self.book_url)
            resp.raise_for_status()
            self.raw_content = resp.text.lower()
        except requests.RequestException as e:
            raise WordSourceException(f"Error descargando libro de PG: {e}")

    def _extract_book_id(self):
        match = re.search(r"/(\d+)/?", self.book_url)
        if match:
            return match.group(1)
        return "unknown"
