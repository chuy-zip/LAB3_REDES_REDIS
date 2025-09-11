import asyncio
import time
import json
from src.algorithms.dijkstra import Dijkstra

class SimpleLSR:
    def __init__(self):
        self.node = None
        self.running = False
        self.seen_messages = set()
        self.dijkstra = Dijkstra()

    def set_node(self, node):
        self.node = node
        self.dijkstra.set_node(node)

    def handle_message(self, message):
        """Manejar mensajes recibidos"""
        message_type = message.get('type')

        if message_type == 'hello':
            self._handle_hello(message)
        elif message_type == 'message':
            self._handle_routing_message(message)

    def _handle_hello(self, message):
        """Manejar mensajes hello - resetear timer"""
        try:
            from_node = message['from']
            to_node = message['to']
            hops = message['hops']

            # Solo procesar si es para este nodo
            #if to_node != self.node.node_id:
            #    return

            self.node.logger.info(f"Hello recibido de nodo: {from_node}")

            # Asegurarnos de que la estructura de la tabla exista
            if self.node.node_id not in self.node.routing_table:
                self.node.routing_table[self.node.node_id] = {}

            # Verificar si es una reconexión (nuevo vecino o reconexión)
            was_reconnection = from_node not in self.node.routing_table[self.node.node_id]

            # Actualizar timer en la tabla de routing
            if from_node in self.node.routing_table[self.node.node_id]:
                self.node.routing_table[self.node.node_id][from_node]['time'] = 15
                self.node.logger.debug(f"Timer resetado para {from_node}")
            else:
                # Agregar nuevo vecino (recuperar conexión)
                self.node.routing_table[self.node.node_id][from_node] = {
                    "weight": hops,
                    "time": 15
                }
                self.node.logger.info(f"Vecino reconectado: {from_node}")

            # PROPAGAR INFORMACIÓN SI FUE UNA RECONEXIÓN
            if was_reconnection:
                self.node.logger.info(f"Propagando información de reconexión: {from_node}")
                self._propagate_routing_info()

        except Exception as e:
            self.node.logger.error(f"Error procesando hello: {e}")


    def _handle_routing_message(self, message):
        """Manejar mensajes de routing - actualizar tabla"""
        from_node = message['from']
        to_node = message['to']
        hops = message['hops']

        # En vez de solo ignorar por duplicado, verificamos si hay cambio real
        current_weight = (
            self.node.routing_table.get(from_node, {})
            .get(to_node, {})
            .get("weight")
        )

        if current_weight == hops:
            # No hay cambio, ignoramos flooding
            self.node.logger.debug(
                f"Mensaje repetido sin cambios ignorado: {from_node}->{to_node} ({hops})"
            )
            return

        self.node.logger.info(f"Mensaje obtenido: {message}")

        # Actualizar tabla de routing
        if from_node not in self.node.routing_table:
            self.node.routing_table[from_node] = {}

        self.node.routing_table[from_node][to_node] = {
            "weight": hops
        }

        self.node.logger.info(
            f"---- Tabla inicializada:\n{json.dumps(self.node.routing_table, indent=2)}"
        )

        # Hacer flooding a todos los vecinos excepto al remitente
        asyncio.create_task(
            self.node.flood_message(message, exclude_neighbor=from_node)
        )

    async def start(self):
        """Iniciar el algoritmo LSR"""
        self.running = True
        self.node.logger.info("Algoritmo SimpleLSR iniciado")

        self._propagate_routing_info()

        dijkstra_task = asyncio.create_task(self.dijkstra.start())

        # Tarea para enviar hellos periódicamente
        async def hello_task():
            while self.running:
                await self.node.send_hello()
                await asyncio.sleep(3)  # Hello cada 3 segundos

        # Tarea para decrementar timers
        async def timer_task():
            while self.running:
                await asyncio.sleep(1)
                self._decrement_timers()

        # Iniciar ambas tareas
        hello_task_obj = asyncio.create_task(hello_task())
        timer_task_obj = asyncio.create_task(timer_task())

        try:
            await asyncio.gather(hello_task_obj, timer_task_obj)
        except asyncio.CancelledError:
            self.node.logger.info("SimpleLSR detenido")

    def _decrement_timers(self):
        """Decrementar timers de los vecinos y eliminar nodos expirados de la tabla"""
        expired_nodes = []

        # recorrer toda la tabla y bajar los timers
        for from_node, neighbors in list(self.node.routing_table.items()):
            for to_node, info in list(neighbors.items()):
                if "time" in info:
                    info["time"] -= 1
                    if info["time"] <= 0:
                        expired_nodes.append(to_node)

        # eliminar nodos expirados y todas las rutas asociadas
        for dead in expired_nodes:
            # 1. Eliminar la entrada principal del nodo muerto
            if dead in self.node.routing_table:
                del self.node.routing_table[dead]

            # 2. Eliminar referencias hacia el nodo muerto desde cualquier otro
            for from_node, neighbors in list(self.node.routing_table.items()):
                if dead in neighbors:
                    del neighbors[dead]

        # limpiar nodos que se queden sin vecinos
        for node in list(self.node.routing_table.keys()):
            if not self.node.routing_table[node]:  # Diccionario vacío
                self.node.routing_table[node] = {}

        # logging
        if expired_nodes:
            self.node.logger.info(
                f"Nodos eliminados por timeout: {expired_nodes}\n"
                f"Tabla actual:\n{json.dumps(self.node.routing_table, indent=2)}"
            )
            self._propagate_routing_info()



    def _propagate_routing_info(self):
        """Propagar información de routing a vecinos"""
        # Verificar que tenemos vecinos directos
        if self.node.node_id not in self.node.routing_table:
            return

        # Para cada conexión directa de este nodo
        for neighbor, data in self.node.routing_table[self.node.node_id].items():
            message = {
                "type": "message",
                "from": self.node.node_id,
                "to": neighbor,
                "hops": data['weight']
            }
            # ✅ Agregar logging para debugging
            self.node.logger.info(f"Propagando: {self.node.node_id} -> {neighbor} (peso: {data['weight']})")
            self.node.logger.info(
                f"---- Tabla actualizada:\n{json.dumps(self.node.routing_table, indent=2)}"
            )

            asyncio.create_task(self.node.send_message(message, neighbor))

    def shutdown(self):
        self.running = False
        self.dijkstra.shutdown()