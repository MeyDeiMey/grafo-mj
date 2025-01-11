# Cambios en tu repositorio local# graph/graph.py

# Cambios en tu repositorio local
import networkx as nx
from .node import Node

class Graph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, word: str):
        n = Node(word)
        self.graph.add_node(n)

    def add_edge(self, w1: str, w2: str) -> bool:
        n1 = Node(w1)
        n2 = Node(w2)
        if n1 not in self.graph:
            self.graph.add_node(n1)
        if n2 not in self.graph:
            self.graph.add_node(n2)
        if self._is_one_letter_apart(w1, w2):
            if not self.graph.has_edge(n1, n2):
                self.graph.add_edge(n1, n2)
                return True
        return False

    def _is_one_letter_apart(self, w1, w2):
        if len(w1) != len(w2):
            return False
        return sum(a != b for a, b in zip(w1, w2)) == 1

    def shortest_path(self, w1: str, w2: str):
        """
        Encuentra el camino más corto entre dos palabras.
        """
        return nx.shortest_path(self.graph, Node(w1), Node(w2))

    def clusters(self):
        """
        Obtiene los componentes conectados del grafo.
        """
        return list(nx.connected_components(self.graph))

    def high_connectivity_nodes(self, threshold: int):
        """
        Encuentra nodos con grado mayor o igual al umbral especificado.
        """
        return [n for n in self.graph.nodes if self.graph.degree(n) >= threshold]

    def all_paths(self, w1: str, w2: str, cutoff: int = None):
        """
        Encuentra todos los caminos posibles entre dos palabras.
        
        Args:
            w1 (str): Palabra de origen
            w2 (str): Palabra de destino
            cutoff (int, optional): Longitud máxima del camino
            
        Returns:
            list: Lista de caminos, donde cada camino es una lista de nodos
        """
        n1 = Node(w1)
        n2 = Node(w2)
        if n1 not in self.graph or n2 not in self.graph:
            return []
        return list(nx.all_simple_paths(self.graph, n1, n2, cutoff=cutoff))

    def max_distance_path(self):
        """
        Encuentra el camino más largo sin ciclos en el grafo.
        Implementación para grafos no dirigidos usando fuerza bruta controlada.
        
        Returns:
            list: Lista de nodos que forman el camino más largo
        """
        longest_path = []
        max_length = 0
        
        # Obtener todos los nodos del grafo
        nodes = list(self.graph.nodes())
        
        # Para cada par de nodos, encontrar el camino más largo entre ellos
        for i, source in enumerate(nodes):
            for target in nodes[i+1:]:  # Evitamos pares redundantes
                try:
                    # Encontrar todos los caminos simples entre source y target
                    paths = nx.all_simple_paths(self.graph, source, target)
                    for path in paths:
                        if len(path) > max_length:
                            max_length = len(path)
                            longest_path = path
                except nx.NetworkXNoPath:
                    continue
                except Exception as e:
                    print(f"Error al procesar el par {source}-{target}: {e}")
                    continue
        
        # Si no se encontró ningún camino, devolver lista vacía
        if not longest_path:
            return []
            
        return longest_path

    def get_isolated_nodes(self):
        """
        Encuentra todos los nodos sin conexiones.
        
        Returns:
            list: Lista de nodos aislados
        """
        return list(nx.isolates(self.graph))

    def get_node_degree(self, word: str) -> int:
        """
        Obtiene el grado (número de conexiones) de un nodo.
        
        Args:
            word (str): Palabra para la que queremos obtener el grado
            
        Returns:
            int: Grado del nodo
        """
        node = Node(word)
        if node in self.graph:
            return self.graph.degree(node)
        return 0

    def get_graph_density(self) -> float:
        """
        Calcula la densidad del grafo (proporción de aristas presentes vs posibles).
        
        Returns:
            float: Densidad del grafo entre 0 y 1
        """
        return nx.density(self.graph)

    def get_node_connectivity(self) -> int:
        """
        Calcula la conectividad del grafo.
        
        Returns:
            int: Conectividad del grafo
        """
        try:
            return nx.node_connectivity(self.graph)
        except:
            return 0

    def __repr__(self):
        return f"Graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges."
