from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import sys
import os

# Allow relative imports to work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database_setup import get_db_connection
from blueprints.admin_routes import admin_routes
from blueprints.manager_routes import manager_routes
from blueprints.booking_routes import booking_routes

bcrypt = Bcrypt()
mail = Mail()  # ✅ Only declare once

def create_app(testing=False):
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

    # Mail config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'foyezahammed897@gmail.com'
    app.config['MAIL_PASSWORD'] = 'isec jfia ppic vvmf'

    if testing:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['MAIL_SUPPRESS_SEND'] = True  # Prevents real emails during tests

    # Initialize extensions
    bcrypt.init_app(app)
    mail.init_app(app)
    JWTManager(app)

    # Register Blueprints
    app.register_blueprint(admin_routes)
    app.register_blueprint(manager_routes)
    app.register_blueprint(booking_routes)

    return app