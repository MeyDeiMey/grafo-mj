# main.py

import os
import sys

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.word_manager import WordManager
from word_sources.local_dictionary_word_source import LocalDictionaryWordSource
from word_sources.project_gutenberg_word_source import ProjectGutenbergWordSource
from word_sources.exceptions import WordSourceException
from config import DATA_LAKE_PATH, DATA_MART_PATH

def main():
    print("Seleccione la fuente de datos:")
    print("1. Archivo de diccionario local")
    print("2. Libro de Project Gutenberg")
    option = input("Ingrese 1 o 2: ")

    try:
        if option == '1':
            file_path = input("Ingrese la ruta al archivo de diccionario local: ")
            word_source = LocalDictionaryWordSource(file_path)
        elif option == '2':
            book_url = input("Ingrese la URL del libro de Project Gutenberg: ")
            word_source = ProjectGutenbergWordSource(book_url)
        else:
            print("Opción no válida")
            return

        word_manager = WordManager(word_source)
        new_words_count = word_manager.process_words(DATA_LAKE_PATH, DATA_MART_PATH)
        print("Procesamiento completado.")
        
        # Mostrar cuántas palabras nuevas se añadieron
        total_new_words = sum(new_words_count.values())
        print(f"Número total de palabras nuevas añadidas: {total_new_words}")
        for length, count in sorted(new_words_count.items()):
            print(f"Longitud {length}: {count} palabras nuevas")
    except (WordSourceException, ValueError, IOError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
