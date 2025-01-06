# word_manager.py

import os
from typing import Dict, Set
from word_sources.word_source import WordSource

class WordManager:
    def __init__(self, word_source: WordSource):
        self.word_source = word_source

    def process_words(self, data_lake_path: str, data_mart_path: str) -> Dict[int, int]:
        """
        1) Guarda los datos crudos en datalake/.
        2) get_words() => {longitud: set(...)}, y guarda en datamart/ words_{n}.txt sin duplicados.
        Retorna {n: num_palabras_nuevas} para cada longitud n.
        """
        new_words_count = {}

        # 1) Guardar data cruda
        self.word_source.save_raw_data(data_lake_path)

        # 2) Obtener palabras y guardar en datamart
        words_by_length = self.word_source.get_words()
        if not os.path.isdir(data_mart_path):
            os.makedirs(data_mart_path)

        for length, word_set in words_by_length.items():
            file_name = f"words_{length}.txt"
            file_path = os.path.join(data_mart_path, file_name)

            existing = set()
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = {line.strip() for line in f if line.strip()}

            new_set = word_set - existing
            new_words_count[length] = len(new_set)

            combined = existing.union(word_set)
            with open(file_path, 'w', encoding='utf-8') as f:
                for w in sorted(combined):
                    f.write(w + "\n")

        return new_words_count
