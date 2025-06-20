from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_admin import Admin

mongo = PyMongo()
jwt = JWTManager()
cors = CORS()
admin = Admin(name='ExoPlanet Admin', template_mode='bootstrap3')