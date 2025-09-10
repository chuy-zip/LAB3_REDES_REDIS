import heapq
import asyncio
import json
from src.utils.logger import setup_logger

class Dijkstra:
    def __init__(self):
        self.node = None
        self.logger = setup_logger("Dijkstra-Init")
        self.routing_table = {}
        self.topology = {}
        self.running = True
        
    def set_node(self, node):
        self.node = node
        # Actualizar logger con ID del nodo una vez que tenemos la referencia
        self.logger = setup_logger(f"Dijkstra-{self.node.node_id}")
        self.logger.info("Logger configurado con ID de nodo")
        
    def build_topology_from_config(self, topo_config):
        # Construye la topología completa desde el archivo de configuración
        if "config" in topo_config:
            self.topology = topo_config["config"]
            self.logger.info(f"Topología cargada con {len(self.topology)} nodos")
            self.logger.debug(f"Topología detallada: {self.topology}")
        else:
            self.logger.error("Formato de topología inválido - falta clave 'config'")
        
        return self.topology
    
    def calculate_routes(self):
        # Calcula las rutas más cortas usando Dijkstra
        if not self.topology:
            self.logger.error("No hay topología para calcular rutas")
            return False
            
        start_node = self.node.node_id
        self.logger.info(f"Calculando rutas desde nodo {start_node}")
        
        distances = {node: float('inf') for node in self.topology}
        distances[start_node] = 0
        previous = {node: None for node in self.topology}
        
        # Cola de prioridad
        pq = [(0, start_node)]
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            # Si encontramos una distancia mejor, la ignoramos
            if current_distance > distances[current_node]:
                continue
                
            # Explorar vecinos
            for neighbor, weight in self.topology[current_node].items():
                distance = current_distance + weight
                
                # Si encontramos un camino más corto
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        # Construir tabla de routing
        self.routing_table = {}
        for node in self.topology:
            if node != start_node:
                # Reconstruir el camino
                path = []
                current = node
                while current is not None:
                    path.append(current)
                    current = previous[current]
                path.reverse()
                
                # El next hop es el primer nodo en el camino
                if len(path) > 1:
                    next_hop = path[1]
                    self.routing_table[node] = {
                        'next_hop': next_hop,
                        'cost': distances[node],
                        'path': path
                    }
        
        self.logger.info(f"Tabla de routing calculada para {len(self.routing_table)} destinos")
        for dest, info in self.routing_table.items():
            self.logger.debug(f"Ruta a {dest}: {info['path']} (costo: {info['cost']})")
        
        return True
        
    def get_next_hop(self, destination):
        if destination in self.routing_table:
            return self.routing_table[destination]['next_hop']
        self.logger.warning(f"No hay ruta conocida para {destination}")
        return None
        
    async def handle_message_async(self, message):
        message_type = message.get("type", "")
        destination = message.get("to", "")
        message_id = message.get("id", "unknown")
        
        self.logger.debug(f"Mensaje recibido [ID: {message_id}, Type: {message_type}, To: {destination}]")
        
        if message_type == "message":
            if destination == self.node.node_id:
                self.logger.info(f"✓ Mensaje destinado a nosotros: {message.get('payload', '')}")
            else:
                next_hop = self.get_next_hop(destination)
                if next_hop:
                    success = await self.node.send_message(message, next_hop)
                    if success:
                        self.logger.info(f"✓ Mensaje forwardeado a {next_hop} para {destination}")
                    else:
                        self.logger.error(f"X No se pudo enviar a {next_hop}")
                else:
                    self.logger.error(f"X No hay ruta para {destination}")
        else:
            self.logger.debug(f"Mensaje tipo '{message_type}' ignorado por Dijkstra")
        
    async def start(self):
        if self.node:
            self.logger.info(f"Algoritmo Dijkstra iniciado para nodo {self.node.node_id}")
        else:
            self.logger.warning("Algoritmo Dijkstra iniciado sin referencia a nodo")
        while self.running:
            await asyncio.sleep(360)
        
    def update_topology(self, new_topology):
        self.topology = new_topology
        self.logger.info("Topología actualizada, recalculando rutas...")
        self.calculate_routes()