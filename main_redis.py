import asyncio
import sys
import argparse
from src.utils.config_loader import load_config, get_node_addresses, get_neighbors
from src.network.node_redis import RedisNode
from src.algorithms.flooding import Flooding

async def main():
    parser = argparse.ArgumentParser(description='Nodo de red con Redis')
    parser.add_argument('node_id', help='ID del nodo (ej: nodo0, nodo1)')
    parser.add_argument('--algorithm', '-a', default='flooding', 
                        choices=['flooding', 'dijkstra', 'lsr', 'dvr'],
                        help='Algoritmo de enrutamiento a usar')
    
    args = parser.parse_args()
    node_id = args.node_id
    algorithm_name = args.algorithm
    
    # Cargar configuración
    try:
        topo_config = load_config('config/topo-redis.json')
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return
    
    # Obtener información del nodo
    neighbors = get_neighbors(topo_config, node_id)
    
    # Crear algoritmo de routing
    if algorithm_name == 'flooding':
        routing_algorithm = Flooding()
    else:
        print(f"Algoritmo {algorithm_name} no implementado aún, usando flooding")
        routing_algorithm = Flooding()
    
    # Crear e iniciar el nodo
    node = RedisNode(node_id, list(neighbors.keys()), routing_algorithm)
    
    try:
        await node.start()
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando nodo")
    except Exception as e:
        print(f"Error iniciando nodo: {e}")
    finally:
        await node.stop()

if __name__ == '__main__':
    asyncio.run(main())