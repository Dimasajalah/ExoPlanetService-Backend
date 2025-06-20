import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/exoplanets_db")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")