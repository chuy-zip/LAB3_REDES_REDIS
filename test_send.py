import asyncio
import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def send_test_message():
    # Conectar a Redis
    r = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        password=os.getenv("REDIS_PASSWORD")
    )
    
    # Mensaje de prueba
    message = {
        "proto": "flooding",
        "type": "message",
        "from": "TEST",
        "to": "N1",  # Destino
        "ttl": 10,
        "headers": [],
        "payload": "Mensaje de prueba manual",
        "timestamp": 1234567890
    }
    
    # Publicar en canal de N1
    await r.publish("sec30.grupo5.N5", json.dumps(message))
    print("Mensaje enviado a N1")
    await r.close()

asyncio.run(send_test_message())