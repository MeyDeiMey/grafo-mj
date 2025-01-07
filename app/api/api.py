# api/api.py

from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import sys
import pickle
import networkx as nx
import logging

# Asegurarse de que Python reconozca la carpeta raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATA_MART_PATH
from graph.graph import Graph

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar el grafo serializado
graph = Graph()
is_initialized = False

def load_graph():
    global is_initialized
    try:
        # Ajustar la ruta para apuntar a graphword-mj en lugar de app/api
        serialized_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'graph.pkl')
        if not os.path.isfile(serialized_path):
            logger.error(f"Archivo serializado del grafo no encontrado en {serialized_path}")
            return False
        with open(serialized_path, 'rb') as f:
            graph.graph = pickle.load(f)
        is_initialized = True
        logger.info(f"Grafo cargado exitosamente desde {serialized_path}: {graph.graph.number_of_nodes()} nodos, {graph.graph.number_of_edges()} aristas.")
        return True
    except Exception as e:
        logger.error(f"Error al cargar el grafo serializado: {e}", exc_info=True)
        return False

# Cargar el grafo al iniciar la aplicación
if load_graph():
    logger.info("La aplicación ha iniciado con el grafo ya cargado.")
else:
    logger.error("La aplicación ha iniciado sin un grafo cargado.")

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Bienvenido a la API de Grafos",
        "endpoints": {
            "GET /shortest-path?word1=...&word2=...": "Obtiene el camino más corto entre dos palabras",
            "GET /clusters": "Retorna los componentes conectados del grafo",
            "GET /high-connectivity?degree=2": "Retorna los nodos con grado >= 2"
        }
    })

@app.route("/shortest-path", methods=["GET"])
def get_shortest_path():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado correctamente."}), 500
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
        logger.error(f"Error al encontrar el camino más corto: {e}", exc_info=True)
        return jsonify({"error": f"Error al encontrar el camino más corto: {str(e)}"}), 500

@app.route("/clusters", methods=["GET"])
def get_clusters():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado correctamente."}), 500
    try:
        clusters = graph.clusters()
        cluster_list = [list(cluster) for cluster in clusters]
        return jsonify({"clusters": cluster_list})
    except Exception as e:
        logger.error(f"Error al obtener clusters: {e}", exc_info=True)
        return jsonify({"error": f"Error al obtener clusters: {str(e)}"}), 500

@app.route("/high-connectivity", methods=["GET"])
def get_high_connectivity():
    if not is_initialized:
        return jsonify({"error": "Grafo no inicializado correctamente."}), 500
    degree = request.args.get("degree", 2, type=int)
    try:
        nodes = graph.high_connectivity_nodes(degree)
        return jsonify({"nodes": [n.word for n in nodes]})
    except Exception as e:
        logger.error(f"Error al obtener nodos de alta conectividad: {e}", exc_info=True)
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
