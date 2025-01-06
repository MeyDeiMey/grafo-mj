# api/api.py

from flask import Flask, request, jsonify
import os
import sys
import networkx as nx

# Asegurarse de que Python reconozca la carpeta raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATA_MART_PATH
from graph.graph import Graph

app = Flask(__name__)

graph = Graph()
is_initialized = False

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Bienvenido a la API de Grafos",
        "endpoints": {
            "POST /initialize": "Construye el grafo a partir de datamart/",
            "GET /shortest-path?word1=...&word2=...": "Obtiene el camino más corto entre dos palabras",
            "GET /clusters": "Retorna los componentes conectados del grafo",
            "GET /high-connectivity?degree=2": "Retorna los nodos con grado >= 2"
        }
    })

@app.route("/initialize", methods=["POST"])
def initialize_graph():
    global is_initialized
    try:
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
            return jsonify({"error": "No se encontraron palabras en datamart."}), 400

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

        is_initialized = True
        return jsonify({
            "message": "Grafo construido a partir de archivos datamart",
            "nodes": len(graph.graph.nodes),
            "edges": len(graph.graph.edges)
        })
    except Exception as e:
        return jsonify({"error": f"Error al construir el grafo: {str(e)}"}), 500

@app.route("/shortest-path", methods=["GET"])
def get_shortest_path():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado. Haz POST a /initialize primero."}), 400
    w1 = request.args.get("word1")
    w2 = request.args.get("word2")
    if not w1 or not w2:
        return jsonify({"error": "Faltan parámetros: word1 y word2."}), 400

    try:
        path = graph.shortest_path(w1, w2)
        return jsonify({"path": [node.word for node in path]})
    except nx.NetworkXNoPath:
        return jsonify({"message": "No se encontró un camino entre las palabras dadas."}), 404
    except Exception as e:
        return jsonify({"error": f"Error al encontrar el camino más corto: {str(e)}"}), 500

@app.route("/clusters", methods=["GET"])
def get_clusters():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado. Haz POST a /initialize primero."}), 400
    try:
        clusters = graph.clusters()
        cluster_list = [list(cluster) for cluster in clusters]
        return jsonify({"clusters": cluster_list})
    except Exception as e:
        return jsonify({"error": f"Error al obtener clusters: {str(e)}"}), 500

@app.route("/high-connectivity", methods=["GET"])
def get_high_connectivity():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado. Haz POST a /initialize primero."}), 400
    degree = request.args.get("degree", 2, type=int)
    try:
        nodes = graph.high_connectivity_nodes(degree)
        return jsonify({"nodes": [n.word for n in nodes]})
    except Exception as e:
        return jsonify({"error": f"Error al obtener nodos de alta conectividad: {str(e)}"}), 500

@app.route("/routes", methods=["GET"])
def list_routes():
    import urllib
    output = {}
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        url = urllib.parse.unquote(str(rule))
        output[url] = methods
    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
