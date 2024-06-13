import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())



class Config:

    # MongoDB configuration
    MONGO_URI = os.environ.get('MONGO_URI') 
    MONGO_DB_NAME = str(os.environ.get('MONGO_DB_NAME')).strip()

    # Redis configuration for Flask Limiter
    REDIS_URI = os.environ.get('REDIS_URI') 

