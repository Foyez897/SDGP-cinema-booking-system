import sqlite3
import bcrypt

def create_new_admin(username, password):
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Connect to the database
    conn = sqlite3.connect("horizon_cinemas.db")
    cursor = conn.cursor()

    # Insert new admin user
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, 'admin'))
    
    conn.commit()
    conn.close()
    print(f"✅ New admin '{username}' created successfully!")

# Create a new admin
create_new_admin("admin2", "Admin@123")