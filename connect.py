"""HealthLink: conexiones a las bases de datos.

Levantar los contenedores antes de correr el proyecto:
    docker run --name mongodb -d -p 27017:27017 mongo
    docker run --name cassandra -d -p 9042:9042 cassandra
    docker run --name dgraph -d -p 8080:8080 -p 9080:9080 dgraph/standalone:latest
    docker run --name ratel -d -p 8000:8000 dgraph/ratel:latest   (opcional, UI de Dgraph)
"""

import pydgraph
from cassandra.cluster import Cluster
from pymongo import MongoClient

# -------------------
"""
MONGODB
"""

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "healthlink"


def conectar_mongo():
    """Regresa la base healthlink de MongoDB."""
    cliente = MongoClient(MONGO_URI)
    return cliente[MONGO_DB]


# -------------------
"""
CASSANDRA
"""

CASSANDRA_KEYSPACE = "healthlink"


def conectar_cassandra():
    """Regresa la sesión de Cassandra ya dentro del keyspace healthlink (lo crea si no existe)."""
    cluster = Cluster(["127.0.0.1"])   # nodo del contenedor (puerto 9042)
    session = cluster.connect()
    # replication_factor 1: solo hay un nodo, así que solo cabe una copia de cada dato.
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
    """)
    session.set_keyspace(CASSANDRA_KEYSPACE)
    return session


# -------------------
"""
DGRAPH
"""

DGRAPH_URI = "localhost:9080"


def conectar_dgraph():
    """Regresa (client_stub, client). Hay que cerrar el stub al terminar con client_stub.close()."""
    client_stub = pydgraph.DgraphClientStub(DGRAPH_URI)
    client = pydgraph.DgraphClient(client_stub)
    return client_stub, client


if __name__ == "__main__":
    db = conectar_mongo()
    print("MongoDB conectado. Colecciones:", db.list_collection_names())

    session = conectar_cassandra()
    print("Cassandra conectado. Keyspace:", session.keyspace)
    session.cluster.shutdown()

    stub, client = conectar_dgraph()
    client.txn(read_only=True).query("{ q(func: has(dgraph.type), first: 1) { uid } }")
    print("Dgraph conectado.")
    stub.close()
