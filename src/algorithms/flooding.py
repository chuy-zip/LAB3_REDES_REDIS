import asyncio
import time

class Flooding:
    def __init__(self):
        self.node = None
        self.seen_messages = set()
        self.running = False

    def set_node(self, node):
        self.node = node

    def handle_message(self, message):
        # Crear ID único para el mensaje
        message_id = f"{message.get('from', '')}_{message.get('to', '')}_{message.get('payload', '')}_{message.get('timestamp', 0)}"
    
        # Verificar si ya se vio este mensaje
        if message_id in self.seen_messages:
            self.node.logger.info(f" MENSAJE DUPLICADO, IGNORADO: {message.get('payload')}")
            return
        
        self.seen_messages.add(message_id)
        
        # Manejar TTL
        ttl = message.get('ttl', 10) - 1
        if ttl <= 0:
            self.node.logger.debug("TTL agotado")
            return
        
        message['ttl'] = ttl
        
        # Verificar si es para este nodo
        if message.get('to') == self.node.node_id:
            self.node.logger.info(f"MENSAJE RECIBIDO, LLEGO AL DESTINO: {message.get('payload')}")
        else:
            # Reenviar a todos los vecinos excepto al remitente
            asyncio.create_task(
                self.node.flood_message(message, exclude_neighbor=message.get('from'))
            )

    async def start(self):
        self.running = True
        self.node.logger.info("Algoritmo de flooding iniciado")
        
        while self.running:
            await asyncio.sleep(1)

    def shutdown(self):
        self.running = False