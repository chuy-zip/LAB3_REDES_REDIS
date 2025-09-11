import heapq
import json
import asyncio
from typing import Dict, List, Tuple

class Dijkstra:
    def __init__(self):
        self.node = None
        self.running = False
        self.graph = {}
        
    def set_node(self, node):
        self.node = node
        
    def build_graph_from_routing_table(self):
        """Build a graph from the routing table"""
        self.graph = {}
        
        # Add all nodes to the graph
        for node in self.node.routing_table.keys():
            self.graph[node] = {}
        
        # Add edges from routing table
        for source, neighbors in self.node.routing_table.items():
            for target, info in neighbors.items():
                if 'weight' in info:
                    self.graph[source][target] = info['weight']
                    # Ensure bidirectional connection
                    if target not in self.graph:
                        self.graph[target] = {}
                    self.graph[target][source] = info['weight']
    
    def calculate_shortest_paths(self) -> Dict[str, Tuple[int, List[str]]]:
        """Calculate shortest paths from current node to all other nodes"""
        if self.node.node_id not in self.graph:
            return {}
            
        # Initialize distances and predecessors
        distances = {node: float('infinity') for node in self.graph}
        predecessors = {node: None for node in self.graph}
        distances[self.node.node_id] = 0
        
        # Priority queue
        priority_queue = [(0, self.node.node_id)]
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_distance > distances[current_node]:
                continue
                
            for neighbor, weight in self.graph[current_node].items():
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    predecessors[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        # Build paths
        paths = {}
        for node in self.graph:
            if node == self.node.node_id:
                continue
                
            if distances[node] == float('infinity'):
                continue
                
            # Reconstruct path
            path = []
            current = node
            while current is not None:
                path.insert(0, current)
                current = predecessors[current]
                
            paths[node] = (distances[node], path)
            
        return paths
    
    async def print_shortest_paths_periodically(self):
        """Periodically calculate and print shortest paths"""
        while self.running:
            await asyncio.sleep(15)  # Wait 15 seconds
            
            self.build_graph_from_routing_table()
            paths = self.calculate_shortest_paths()
            
            # Format output
            output = f"\nDIJKSTRA DEL NODO {self.node.node_id}:\n\n"
            for target, (distance, path) in paths.items():
                output += f"Camino más corto a {target} (distancia: {distance}):\n"
                for node in path[1:]:  # Skip the first node (current node)
                    output += f" -> pasar por {node}\n"
                output += "\n"
            
            # Print to stdout (can be redirected to another terminal)
            print(output, flush=True)
    
    async def start(self):
        """Start the Dijkstra algorithm"""
        self.running = True
        self.node.logger.info("Algoritmo Dijkstra iniciado")
        
        # Start periodic printing
        asyncio.create_task(self.print_shortest_paths_periodically())
        
        while self.running:
            await asyncio.sleep(1)
    
    def shutdown(self):
        self.running = False