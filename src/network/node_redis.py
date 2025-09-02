import asyncio
import os
import redis.asyncio as redis
import json
import time
from src.utils.logger import setup_logger
from dotenv import load_dotenv
from dotenv import find_dotenv

load_dotenv(find_dotenv())

class RedisNode:
    def __init__(self, node_id, neighbors, routing_algorithm):
        self.node_id = node_id
        self.neighbors = neighbors  # Lista de IDs de nodos vecinos
        self.routing_algorithm = routing_algorithm
        self.logger = setup_logger(node_id)
        self.running = False
        
        # Configuración de Redis
        self.host = os.getenv("REDIS_HOST", "localhost")

        print(f"El host es: {self.host}")
        self.port = os.getenv("REDIS_PORT", 6379)
        self.password = os.getenv("REDIS_PASSWORD", None)
        
        # Canal propio del nodo
        self.my_channel = f"sec30.grupo5.{node_id}"
        
        # Canales a los que suscribirse (vecinos)
        self.neighbor_channels = [f"sec30.grupo5.{neighbor}" for neighbor in neighbors]
        
        self.routing_algorithm.set_node(self)
    
    async def connect_redis(self):
        """Conectar a Redis"""
        try:
            if self.password:
                self.redis = redis.Redis(
                    host=self.host, 
                    port=self.port, 
                    password=self.password
                )
            else:
                self.redis = redis.Redis(
                    host=self.host, 
                    port=self.port
                )
            
            # Probar conexión
            await self.redis.ping()
            self.logger.info(f"Conectado a Redis en {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando a Redis: {e}")
            return False
    
    async def listener(self):
        """Escuchar mensajes en el canal propio"""
        async with self.redis.pubsub() as pubsub:
            # Suscribirse al canal propio
            await pubsub.subscribe(self.my_channel)
            self.logger.info(f"Suscrito al canal: {self.my_channel}")
            
            while self.running:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    
                    if message and message["type"] == "message":
                        # Decodificar mensaje JSON
                        try:
                            message_data = json.loads(message["data"].decode())
                            self.logger.info(f"Mensaje recibido: {message_data}")
                            
                            # Procesar con el algoritmo de routing
                            if hasattr(self.routing_algorithm, 'handle_message_async'):
                                await self.routing_algorithm.handle_message_async(message_data)
                            else:
                                # Fallback al método síncrono
                                self.routing_algorithm.handle_message(message_data)
                            
                        except json.JSONDecodeError:
                            self.logger.error("Mensaje JSON mal formado")
                            
                except Exception as e:
                    self.logger.error(f"Error en listener: {e}")
                    await asyncio.sleep(1)
    
    async def send_message(self, message, neighbor_id):
        """Enviar mensaje a un vecino específico"""
        try:
            target_channel = f"sec30.grupo5.{neighbor_id}"
            message_str = json.dumps(message)
            await self.redis.publish(target_channel, message_str)
            self.logger.debug(f"Mensaje enviado a {neighbor_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a {neighbor_id}: {e}")
            return False
    
    async def flood_message(self, message, exclude_neighbor=None):
        """Enviar mensaje a todos los vecinos"""
        sent_count = 0
        for neighbor_id in self.neighbors:
            if neighbor_id != exclude_neighbor:
                if await self.send_message(message, neighbor_id):
                    sent_count += 1
        return sent_count
    
    async def start(self):
        """Iniciar el nodo"""
        self.running = True
        
        if not await self.connect_redis():
            return False
        
        self.logger.info(f"Nodo {self.node_id} iniciado. Vecinos: {self.neighbors}")
        
        # Iniciar algoritmo de routing
        routing_task = asyncio.create_task(self.routing_algorithm.start())
        
        # Iniciar listener
        listener_task = asyncio.create_task(self.listener())
        
        # Esperar a que terminen (o hasta que se detenga)
        try:
            await asyncio.gather(routing_task, listener_task)
        except asyncio.CancelledError:
            self.logger.info("Nodo detenido")
        except Exception as e:
            self.logger.error(f"Error en nodo: {e}")
    
    async def stop(self):
        """Detener el nodo"""
        self.running = False
        if hasattr(self, 'redis'):
            await self.redis.close()
        self.logger.info("Nodo detenido")