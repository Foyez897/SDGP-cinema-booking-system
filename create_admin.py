from database_setup import get_db_connection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
username = "admin"
password = "admin123"  # Change this to your desired password
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, "admin"))
    conn.commit()

print("✅ Admin user created successfully!")