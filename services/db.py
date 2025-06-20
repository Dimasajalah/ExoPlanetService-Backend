import os
from flask_pymongo import PyMongo
from dotenv import load_dotenv

load_dotenv()

mongo = PyMongo()
MONGO_URI = os.getenv("MONGO_URI")
