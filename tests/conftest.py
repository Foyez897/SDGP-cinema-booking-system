import os
import sys
import pytest
from flask_jwt_extended import JWTManager

# Add app directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # ✅ No need to import db if not using SQLAlchemy

@pytest.fixture(scope="function")
def client():
    app = create_app(testing=True)
    JWTManager(app)  # ✅ Ensure JWTManager is initialized

    with app.test_client() as client:
        with app.app_context():
            yield client