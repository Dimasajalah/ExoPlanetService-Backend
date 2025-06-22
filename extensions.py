from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_admin import Admin

mongo = PyMongo()
jwt = JWTManager()
cors = CORS(
    resources={r"/*": {"origins": "https://exo-planet-service-frontend-n5ig-5cmpfimi1.vercel.app"}},
    supports_credentials=True
)
admin = Admin(name='ExoPlanet Admin', template_mode='bootstrap3')
