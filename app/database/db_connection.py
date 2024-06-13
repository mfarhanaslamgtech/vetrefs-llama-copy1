from pymongo import MongoClient
from config.config import Config

def db_connector():
    """
    Establishes a connection to the MongoDB database using the configuration from Config class.
    """
    mongo_client = MongoClient(Config.MONGO_URI)
    db = mongo_client[Config.MONGO_DB_NAME]
    return db

