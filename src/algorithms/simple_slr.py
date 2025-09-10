import asyncio
import time
import json

class SimpleLSR:
    def __init__(self):
        self.node = None
        self.running = False
        self.seen_messages = set()

    def set_node(self, node):
        self.node = node

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
            if to_node != self.node.node_id:
                return
            
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
        
        # Crear ID único para evitar procesamiento duplicado
        message_id = f"{from_node}_{to_node}_{hops}"
        
        if message_id in self.seen_messages:
            self.node.logger.info(f"Mensaje duplicado ignorado: {message_id}")
            return
        
        self.node.logger.info(f"Mensaje obtenido: {message}")
        self.seen_messages.add(message_id)
        
        # Actualizar tabla de routing SIN timer para conexiones aprendidas
        if from_node not in self.node.routing_table:
            self.node.routing_table[from_node] = {}
        
        self.node.routing_table[from_node][to_node] = {
            "weight": hops
        }
        
        self.node.logger.info(f"Tabla actualizada:\n{json.dumps(self.node.routing_table, indent=2)}")
        
        # Hacer flooding a todos los vecinos excepto al remitente
        asyncio.create_task(
            self.node.flood_message(message, exclude_neighbor=from_node)
        )

    async def start(self):
        """Iniciar el algoritmo LSR"""
        self.running = True
        self.node.logger.info("Algoritmo SimpleLSR iniciado")

        self._propagate_routing_info()
        
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
        """Decrementar timers solo de vecinos directos"""
        connections_to_remove = []
        
        # Solo decrementar timers de vecinos directos (nodo propio)
        if self.node.node_id in self.node.routing_table:
            for neighbor, data in self.node.routing_table[self.node.node_id].items():
                data['time'] -= 1
                
                if data['time'] <= 0:
                    connections_to_remove.append(neighbor)
                    self.node.logger.info(f"Vecino directo {neighbor} marcado como inactivo")
        
        # Eliminar conexiones inactivas
        for neighbor in connections_to_remove:
            del self.node.routing_table[self.node.node_id][neighbor]
        
        # Si hay cambios en vecinos directos, propagar la información
        if connections_to_remove:
            self.node.logger.info(f"Propagando cambios por vecinos eliminados: {connections_to_remove}")
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
            asyncio.create_task(self.node.send_message(message, neighbor))

    def shutdown(self):
        self.running = False