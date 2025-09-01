# Algoritmos de enrutamiento en redis

La idea de esta implementación es la misma que la parte con soquets de este lab. Se tiene una clase nodo que implementa un algoritmo dependiendo del comando de ejecución.

##### Grupo 5

#### Dependencias
```
pip install redis
pip install dotenv
```
## Levantar un nodo individual
```
python main_redis.py N1 --algorithm flooding
```

## mandar un mensaje de prueba
Este mensaje de prueba debe de mandarse entre nodos ya inicializados

```
python test_send.py
```

## Probar con test_network.py
Levanta todos los nodos de la topología por separado para poder hacer pruebas.

#### Usar flooding (por defecto)
python tests/run_redis_network.py

#### Usar dijkstra
python tests/run_redis_network.py --algorithm dijkstra

#### Usar forma abreviada
python tests/run_redis_network.py -a lsr

#### Usar distance vector
python tests/run_redis_network.py --algorithm flooding

