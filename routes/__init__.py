from routes.auth import auth_blueprint  # Changed to absolute import
from routes.radial_velocity import radial_velocity_bp
from routes.predict_mass import predict_mass_bp
from .cnn_models import cnn_models_bp
from routes.admin_route import admin_bp
 
def init_routes(app):
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(radial_velocity_bp, url_prefix="/api")
    app.register_blueprint(predict_mass_bp, url_prefix="/api")
    app.register_blueprint(cnn_models_bp, url_prefix="/api/cnn-models") 
    app.register_blueprint(admin_bp)

