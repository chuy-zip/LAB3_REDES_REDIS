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
    
    # Mensaje de prueba tipo "message" (para flooding)
    message = {
        "type": "message",
        "from": "sec30.grupo5.nodo5",
        "to": "sec30.grupo5.nodo9",
        "hops": 10  # Este sería el peso/costo entre ellos
    }
    
    # Publicar en canal del nodo 5 (para que lo procese y haga flooding)
    await r.publish("sec30.grupo5.nodo5", json.dumps(message))
    print("Mensaje enviado a sec30.grupo5.nodo5")
    
    # O publicar directamente en canal del nodo 9 (para prueba directa)
    # await r.publish("sec30.grupo5.nodo9", json.dumps(message))
    # print("Mensaje enviado directamente a sec30.grupo5.nodo9")
    
    await r.close()

if __name__ == "__main__":
    asyncio.run(send_test_message())