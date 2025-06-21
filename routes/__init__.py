from routes.auth import auth_blueprint  # Changed to absolute import
from routes.admin_route import admin_bp
 
def init_routes(app):
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(admin_bp)

