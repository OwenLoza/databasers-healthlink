"""HealthLink: conexiones a las bases de datos."""

from pymongo import MongoClient

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


if __name__ == "__main__":
    db = conectar_mongo()
    print("MongoDB conectado. Base:", db.name)
    print("Colecciones:", db.list_collection_names())
