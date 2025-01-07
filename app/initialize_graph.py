# graph/initialize_graph.py

import os
import sys
import pickle
import logging
from graph.graph import Graph

from config import DATA_MART_PATH

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("initialize_graph.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    graph = Graph()
    try:
        logger.info("Iniciando construcción del grafo")
        all_words = set()
        for file_name in os.listdir(DATA_MART_PATH):
            if file_name.startswith("words_") and file_name.endswith(".txt"):
                file_path = os.path.join(DATA_MART_PATH, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        w = line.strip()
                        if w:
                            all_words.add(w)

        if not all_words:
            logger.warning("No se encontraron palabras en datamart.")
            return

        # Construir el grafo
        for w in all_words:
            graph.add_node(w)

        # Añadir edges
        all_words_list = list(all_words)
        total_edges = 0
        for i in range(len(all_words_list)):
            for j in range(i + 1, len(all_words_list)):
                w1 = all_words_list[i]
                w2 = all_words_list[j]
                if graph.add_edge(w1, w2):
                    total_edges += 1

        logger.info(f"Grafo construido exitosamente: {len(graph.graph.nodes)} nodos, {len(graph.graph.edges)} aristas.")

        # Serializar el grafo
        serialized_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graph.pkl')
        with open(serialized_path, 'wb') as f:
            pickle.dump(graph.graph, f)
        logger.info(f"Grafo serializado en {serialized_path}")

    except Exception as e:
        logger.error(f"Error al construir y serializar el grafo: {e}", exc_info=True)

if __name__ == "__main__":
    main()
