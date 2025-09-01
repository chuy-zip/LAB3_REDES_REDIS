import asyncio
import os
import subprocess
import time
import signal
import threading
import json
import argparse
import sys
from dotenv import load_dotenv

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.config_loader import load_config, get_neighbors

load_dotenv()

class RedisNetworkManager:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.logs = {}
        
        # Cargar configuración
        self.topo_config = load_config('config/topo-redis.json')
        self.all_nodes = list(self.topo_config['config'].keys())
    
    def start_all_nodes(self, algorithm='flooding'):
        """Inicia todos los nodos de la red"""
        self.running = True
        print(f"Iniciando todos los nodos de la red con algoritmo: {algorithm}")
        print("Los logs de cada nodo se mostrarán en ventanas separadas")
        print("\n")
        
        for node_id in self.all_nodes:
            self.start_node(node_id, algorithm)
            time.sleep(2)  # Pausa para evitar congestión
        
        print("\n")
        print("Todos los nodos iniciados. Usa el menú para enviar mensajes.")
        print("Presiona Ctrl+C para detener todos los nodos.")
    
    def start_node(self, node_id, algorithm='flooding'):
        """Inicia un nodo específico en una terminal separada"""
        try:
            # Comando para iniciar el nodo
            cmd = [
                sys.executable, "main_redis.py", node_id, "--algorithm", algorithm
            ]
            
            # Iniciar proceso en ventana separada (dependiendo del OS)
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    ['start', 'cmd', '/k'] + cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:  # Unix/Linux/Mac
                process = subprocess.Popen(
                    ['xterm', '-e'] + cmd + [';', 'bash'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            self.processes[node_id] = process
            print(f"Nodo {node_id} iniciado en terminal separada")
            
        except Exception as e:
            print(f"Error iniciando nodo {node_id}: {e}")
    
    def stop_all_nodes(self):
        """Detiene todos los nodos"""
        self.running = False
        print("\nDeteniendo todos los nodos...")
        
        for node_id, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=3)
                print(f"Nodo {node_id} detenido")
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    print(f"Nodo {node_id} forzado a detenerse")
                except:
                    pass
            except Exception as e:
                print(f"Error deteniendo nodo {node_id}: {e}")
    
    async def send_test_message(self, from_node, to_node, message_text, proto="flooding"):
        """Envía un mensaje de prueba usando Redis directamente"""
        try:
            import redis.asyncio as redis
            
            # Conectar a Redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST"),
                port=int(os.getenv("REDIS_PORT")),
                password=os.getenv("REDIS_PASSWORD")
            )
            
            message = {
                "proto": proto,
                "type": "message",
                "from": from_node,
                "to": to_node,
                "ttl": 15,
                "headers": [],
                "payload": message_text,
                "timestamp": int(time.time())
            }
            
            # Publicar en el canal del nodo origen (para simular que este lo envia)
            target_channel = f"sec30.grupo5.{from_node}"
            await r.publish(target_channel, json.dumps(message))
            await r.close()
            
            print(f"Mensaje enviado desde {from_node} a {to_node}: '{message_text}'")
            print("El mensaje se envió al canal del nodo origen para iniciar el flooding")
            
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
    
    def show_topology(self):
        """Muestra la topología de la red"""
        print("\nTOPOLOGÍA DE LA RED:")
        print("\n")
        for node_id, neighbors in self.topo_config['config'].items():
            print(f"{node_id}: {list(neighbors.keys())}")
        print("\n")

async def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Gestor de red Redis para Laboratorio 3')
    parser.add_argument('--algorithm', '-a', default='flooding', 
                       choices=['flooding', 'dijkstra', 'lsr', 'dvr'],
                       help='Algoritmo de enrutamiento a usar')
    parser.add_argument('--send', action='store_true',
                       help='Modo de envío rápido de mensajes')
    parser.add_argument('--from-node', help='Nodo origen para envío rápido')
    parser.add_argument('--to-node', help='Nodo destino para envío rápido')
    parser.add_argument('--message', help='Mensaje para envío rápido')
    
    args = parser.parse_args()
    
    # Modo de envío rápido
    if args.send:
        if not all([args.from_node, args.to_node, args.message]):
            print("Error: Modo send requiere --from-node, --to-node y --message")
            sys.exit(1)
        
        manager = RedisNetworkManager()
        await manager.send_test_message(args.from_node, args.to_node, args.message, args.algorithm)
        return
    
    # Modo completo: iniciar todos los nodos
    manager = RedisNetworkManager()
    
    def signal_handler(sig, frame):
        print("\n\nSeñal de interrupción recibida...")
        manager.stop_all_nodes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar todos los nodos con el algoritmo especificado
    manager.start_all_nodes(args.algorithm)
    
    # Menú interactivo
    try:
        while True:
            print("\n" + "\n")
            print("MENÚ DE PRUEBAS REDIS - LAB3 REDES")
            print("\n")
            print(f"Algoritmo: {args.algorithm}")
            print("1. Enviar mensaje de prueba")
            print("2. Mostrar estado de todos los nodos")
            print("3. Mostrar topología de la red")
            print("4. Reiniciar con diferente algoritmo")
            print("5. Salir y detener todos los nodos")
            print("\n")
            
            choice = input("Selecciona una opción (1-5): ").strip()
            
            if choice == '1':
                print("\n--- ENVIAR MENSAJE ---")
                from_node = input("Nodo origen (ej: N1): ").strip().upper()
                to_node = input("Nodo destino (ej: N5): ").strip().upper()
                message = input("Mensaje: ").strip()
                
                if from_node and to_node and message:
                    await manager.send_test_message(from_node, to_node, message, args.algorithm)
                    print("Mensaje enviado. Revisa las terminales de los nodos.")
                else:
                    print("Error: Debes completar todos los campos")
                
            elif choice == '2':
                manager.show_topology()
                
            elif choice == '3':
                print("\n--- CAMBIAR ALGORITMO ---")
                print("Algoritmos disponibles: flooding, dijkstra, lsr, dvr")
                new_algorithm = input("Nuevo algoritmo: ").strip().lower()
                if new_algorithm in ['flooding', 'dijkstra', 'lsr', 'dvr']:
                    print(f"Reiniciando con algoritmo: {new_algorithm}")
                    manager.stop_all_nodes()
                    args.algorithm = new_algorithm
                    manager = RedisNetworkManager()
                    manager.start_all_nodes(args.algorithm)
                else:
                    print("Algoritmo no válido")
                    
            elif choice == '4':
                print("Saliendo...")
                break
                
            else:
                print("Opción no válida. Por favor elige 1-5.")
                
            # pausa para que se vean los logs
            time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nInterrupción recibida...")
    
    finally:
        manager.stop_all_nodes()

if __name__ == '__main__':
    # Para manejar async en el main
    asyncio.run(main())