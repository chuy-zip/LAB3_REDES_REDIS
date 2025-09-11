import asyncio
import sys
import argparse
from src.utils.config_loader import load_config, get_node_addresses, get_neighbors
from src.network.node_redis import RedisNode
from src.algorithms.flooding import Flooding
from src.algorithms.dijkstra import Dijkstra
from src.algorithms.link_state import LinkStateRouter
from src.algorithms.simple_slr import SimpleLSR

async def main():
    parser = argparse.ArgumentParser(description='Nodo de red con Redis')
    parser.add_argument('node_id', help='ID del nodo (ej: sec30.grupo5.nodo5')
    parser.add_argument('--algorithm', '-a', default='flooding', 
                        choices=['flooding', 'dijkstra', 'lsr', 'lsr_simple'],
                        help='Algoritmo de enrutamiento a usar')
    
    args = parser.parse_args()
    node_id = args.node_id
    algorithm_name = args.algorithm
    
    # Cargar configuración
    try:
        topo_config = load_config('config/topo-redis-test.json')
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return
    
    # Obtener información del nodo
    neighbors = get_neighbors(topo_config, node_id)
    
    # Crear algoritmo de routing
    if algorithm_name == 'flooding':
        routing_algorithm = Flooding()
    elif algorithm_name == 'lsr':
        routing_algorithm = LinkStateRouter()
    elif algorithm_name == 'lsr_simple':
        routing_algorithm = SimpleLSR()  # el nuevo
    elif algorithm_name == 'dijkstra':
        routing_algorithm = Dijkstra() 
    else:
        print(f"Algoritmo {algorithm_name} no implementado aún, usando SimpleLSR")
        routing_algorithm = SimpleLSR()

    print(f"{neighbors}")
    # Crear el nodo
    node = RedisNode(node_id, neighbors, routing_algorithm)
    
    # PARA DIJKSTRA: Ahora que el algoritmo tiene referencia al nodo (seteada en RedisNode.__init__),
    # podemos calcular las rutas
    if algorithm_name == 'dijkstra':
        routing_algorithm.calculate_routes()
    
    try:
        await node.start()
        print(f"Nodo {node_id} iniciado. Vecinos: {list(neighbors.keys())}")
        
        # Mantener el nodo corriendo
        while node.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando nodo")
    except Exception as e:
        print(f"Error iniciando nodo: {e}")
    finally:
        await node.stop()

if __name__ == '__main__':
    asyncio.run(main())