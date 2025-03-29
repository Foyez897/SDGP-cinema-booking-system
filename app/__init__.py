from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from extensions import bcrypt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.database_setup import get_db_connection
from blueprints.admin_routes import admin_routes
from blueprints.manager_routes import manager_routes
from blueprints.booking_routes import booking_routes

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
        static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    )
    app.secret_key = "supersecretkey"

    # JWT configuration
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_HTTPONLY"] = True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 1800
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # Initialize extensions
    bcrypt.init_app(app)          # ✅ Initialize properly
    JWTManager(app)

    # Register Blueprints
    app.register_blueprint(admin_routes)
    app.register_blueprint(manager_routes)
    app.register_blueprint(booking_routes)

    return app  # ✅ Don't forget to return the app!