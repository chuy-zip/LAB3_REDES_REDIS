import asyncio
import os
import redis.asyncio as redis

STOPWORD = "STOP"


async def reader(channel: redis.client.PubSub):
    while True:
        message = await channel.get_message(ignore_subscribe_messages=True, timeout=None)
        if message is not None:
            print(f"(Reader) Message Received: {message}")
            if message["data"].decode() == STOPWORD:
                print("(Reader) STOP")
                break

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
PWD = os.getenv("PWD")

async def main():
    """The main asynchronous function."""
    r = redis.Redis(host=HOST, port=PORT, password=PWD)
    #r = redis.Redis(host=HOST, port=PORT)	#, password=PWD)
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("sec30.grupo0.nodo0")

        future = asyncio.create_task(reader(pubsub))

        await r.publish("sec30.grupo0.nodo0", "Starting Channel")
        #await r.publish("channel:2", "World")
        
        #await r.publish("channel:1", STOPWORD)

        await future

if __name__ == "__main__":
    print("Starting asyncio and redis test...")
    asyncio.run(main())
    print("DONE!")

