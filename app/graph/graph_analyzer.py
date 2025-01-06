# graph/graph_analyzer.py

import networkx as nx
from typing import Optional, List
import matplotlib.pyplot as plt

class GraphAnalyzer:
    """
    Encapsula la lógica de análisis de un grafo de palabras:
      - Info básica: número de nodos, aristas, grado medio...
      - Caminos más cortos
      - Distancia máxima
      - Clústeres
      - Nodos con cierto grado de conectividad
      - Nodos aislados
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def get_basic_info(self) -> dict:
        """
        Retorna info general:
          - number_of_nodes
          - number_of_edges
          - average_degree
          - number_of_connected_components
          - largest_component_size
        """
        n = self.graph.number_of_nodes()
        degree_sum = sum(dict(self.graph.degree()).values())
        connected_components = list(nx.connected_components(self.graph))

        info = {
            'number_of_nodes': n,
            'number_of_edges': self.graph.number_of_edges(),
            'average_degree': degree_sum / n if n > 0 else 0,
            'number_of_connected_components': len(connected_components),
            'largest_component_size': max(len(c) for c in connected_components) if connected_components else 0
        }
        return info

    def get_degree_distribution(self) -> dict:
        """
        Retorna dict { grado: cantidad_de_nodos_con_ese_grado }.
        """
        distribution = {}
        for _, deg in self.graph.degree():
            distribution[deg] = distribution.get(deg, 0) + 1
        return distribution

    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Camino más corto entre 'source' y 'target'.
        Retorna None si no hay camino o si source/target no están en el grafo.
        """
        if source not in self.graph or target not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, source=source, target=target)
            return path
        except nx.NetworkXNoPath:
            return None

    def all_paths(self, source: str, target: str, limit: int = 10) -> List[List[str]]:
        """
        Retorna una lista con todos los caminos simples entre source y target (limitado a 'limit').
        """
        if source not in self.graph or target not in self.graph:
            return []
        paths_generator = nx.all_simple_paths(self.graph, source=source, target=target)
        paths_list = []
        for i, p in enumerate(paths_generator):
            if i >= limit:
                break
            paths_list.append(p)
        return paths_list

    def maximum_distance(self) -> int:
        """
        Distancia máxima entre cualquier par de nodos del grafo.
        """
        max_dist = 0
        for node in self.graph.nodes:
            lengths = nx.single_source_shortest_path_length(self.graph, node)
            max_node_dist = max(lengths.values(), default=0)
            max_dist = max(max_dist, max_node_dist)
        return max_dist

    def clusters(self):
        """
        Retorna una lista de componentes conexas (clusters),
        cada componente es un set de nodos.
        """
        return list(nx.connected_components(self.graph))

    def high_connectivity_nodes(self, threshold: int = 1) -> List[str]:
        """
        Retorna los nodos con un grado >= threshold.
        """
        return [n for n, d in self.graph.degree() if d >= threshold]

    def nodes_by_degree(self, degree: int) -> List[str]:
        """
        Retorna los nodos con un grado == degree.
        """
        return [n for n, d in self.graph.degree() if d == degree]

    def isolated_nodes(self) -> List[str]:
        """
        Retorna lista de nodos sin aristas (aislados).
        """
        return list(nx.isolates(self.graph))
    
    def visualize_graph(self, show_labels: bool = True):
        """
        Dibuja el grafo usando matplotlib. El layout por defecto es 'spring_layout'.
        """
        plt.figure(figsize=(12, 8))  # Ajusta el tamaño a tu gusto
        pos = nx.spring_layout(self.graph)  # Calcula posiciones para cada nodo
        
        # Dibuja los nodos
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_color='lightblue',
            node_size=500,
            alpha=0.8
        )
        
        # Dibuja las aristas
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='gray'
        )
        
        # Dibuja las etiquetas con el nombre de cada nodo (si quieres)
        if show_labels:
            nx.draw_networkx_labels(
                self.graph, pos,
                font_size=10,
                font_color='black'
            )

        # Opcionalmente quita los ejes
        plt.axis('off')

        # Muestra la ventana con el grafo
        plt.title("Visualización del Grafo")
        plt.show()
