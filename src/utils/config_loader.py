import json

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def get_node_addresses(names_config):
    return names_config['config']

def get_neighbors(topo_config, node_id):
    # Devuelve un diccionario de {vecino: costo}
    return topo_config['config'].get(node_id, {})