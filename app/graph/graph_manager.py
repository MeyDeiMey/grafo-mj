# graph/graph_manager.py

from typing import List
from .graph import Graph

class GraphManager:
    """
    Encargado de construir el grafo a partir de una lista de palabras
    y exponer la instancia de Graph.
    """
    def __init__(self):
        self.graph_obj = Graph()

    def build_graph(self, words: List[str]):
        """
        Crea el grafo añadiendo todos los nodos y edges (diferencia de una letra).
        """
        for i, w1 in enumerate(words):
            self.graph_obj.add_node(w1)
            for w2 in words[i+1:]:
                self.graph_obj.add_edge(w1, w2)

    def get_graph(self) -> Graph:
        return self.graph_obj

    def __repr__(self):
        return repr(self.graph_obj)
