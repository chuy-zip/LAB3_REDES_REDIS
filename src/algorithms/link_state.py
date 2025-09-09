import heapq
import time
from src.utils.logger import setup_logger
from src.algorithms.dijkstra import Dijkstra

class LinkStateRouter:
    def __init__(self):
        self.node = None
        self.lsa_seen = set()
        self.topology = {}
        self.routing_table = {}
        self.logger = setup_logger("LSR")
        self.running = True
        self.dijkstra = Dijkstra()

    def set_node(self, node):
        self.node = node

    def send_lsa(self):
        """Enviar LSA de este nodo a todos los vecinos"""
        lsa = {
            "type": "lsa",
            "from": self.node.node_id,
            "neighbors": self.node.neighbors,
            "timestamp": int(time.time()),
            "id": f"{self.node.node_id}_{int(time.time())}"
        }
        self.lsa_seen.add(lsa["id"])
        self.logger.info(lsa)
        self.node.flood_message(lsa)

    def handle_message(self, message):
        msg_type = message.get("type", "")

        if msg_type == "lsa":
            self.handle_lsa(message)
        elif msg_type == "message":
            self.handle_forwarding(message)
        else:
            self.node.logger.debug(f"Ignorando mensaje de tipo {msg_type}")

    def handle_lsa(self, lsa):
        lsa_id = lsa.get("id")
        if lsa_id in self.lsa_seen:
            return

        self.lsa_seen.add(lsa_id)
        sender = lsa["from"]
        neighbors = lsa["neighbors"]

        self.topology[sender] = neighbors
        self.node.logger.info(f"LSA recibida de {sender}: {neighbors}")

        self.calculate_routes()
        self.node.flood_message(lsa, exclude_neighbor=lsa.get("from"))

    def calculate_routes(self):
        if not self.topology:
            return

        start_node = self.node.node_id

        distances = {n: float('inf') for n in self.topology}
        previous = {n: None for n in self.topology}
        distances[start_node] = 0

        pq = [(0, start_node)]

        while pq:
            dist, current = heapq.heappop(pq)
            if dist > distances[current]:
                continue

            for neighbor, cost in self.topology.get(current, {}).items():
                d = dist + cost
                if d < distances[neighbor]:
                    distances[neighbor] = d
                    previous[neighbor] = current
                    heapq.heappush(pq, (d, neighbor))

        self.routing_table = {}
        for node in self.topology:
            if node == start_node:
                continue

            path = []
            cur = node
            while cur is not None:
                path.append(cur)
                cur = previous[cur]
            path.reverse()

            if len(path) > 1:
                self.routing_table[node] = {
                    "next_hop": path[1],
                    "cost": distances[node],
                    "path": path
                }

        self.node.logger.info(f"Tabla de routing recalculada: {self.routing_table}")

    def get_next_hop(self, destination):
        """Obtiene el próximo salto para un destino"""
        if destination in self.routing_table:
            return self.routing_table[destination]['next_hop']

        self.logger.warning(f"No hay ruta conocida para {destination}")
        return None

    def handle_forwarding(self, message):
        destination = message.get("to")
        self.calculate_routes()

        if destination == self.node.node_id:
            self.node.logger.info(f"Mensaje recibido: {message.get('payload')}")
        else:
            next_hop = self.get_next_hop(destination)
            if next_hop:
                self.node.send_message(message, next_hop)
                self.node.logger.info(f"Forwardeando mensaje a {next_hop} para {destination}")
            else:
                self.node.logger.warning(f"No hay ruta para {destination}")

    def start(self):
        self.send_lsa()
        self.node.logger.info("Link State Routing iniciado")
