import sqlite3
import bcrypt

def test_login(username, password):
    conn = sqlite3.connect("horizon_cinemas.db")
    cursor = conn.cursor()

    # Fetch stored hashed password
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print("❌ User not found!")
        return False

    hashed_password = user[0]

    # Compare input password with hashed password
    if bcrypt.checkpw(password.encode(), hashed_password.encode()):
        print("✅ Login successful!")
        return True
    else:
        print("❌ Incorrect password!")
        return False

# Test login
test_login("manager1", "Manager@123")  # Replace with actual password