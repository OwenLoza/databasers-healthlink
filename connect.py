"""HealthLink: conexiones a las bases de datos."""

from pymongo import MongoClient
from cassandra.cluster import Cluster

# -------------------
"""
MONGODB
Levantar el contenedor antes de correr el proyecto:
    docker run --name mongodb -d -p 27017:27017 mongo
"""

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "healthlink"


def conectar_mongo():
    """Regresa la base healthlink de MongoDB. Falla si el contenedor no está arriba."""
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    cliente.admin.command("ping")
    return cliente[MONGO_DB]


def conectar_cassandra():
    """Establece conexión con el contenedor local de Cassandra y retorna la sesión."""
    # Nota: Requiere tener el contenedor de Cassandra corriendo en el puerto 9042
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect('healthlink_keyspace')
    print("Conexión exitosa a Cassandra")
    return session


if __name__ == "__main__":
    db = conectar_mongo()
    print("MongoDB conectado. Base:", db.name)
    print("Colecciones:", db.list_collection_names())
