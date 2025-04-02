from database.database_setup import get_db_connection
import bcrypt

def seed_staff_user():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("staff1",))
    if not cursor.fetchone():
        hashed_pw = bcrypt.hashpw("Staff!Pass789".encode("utf-8"), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("staff1", hashed_pw.decode("utf-8"), "booking_staff"))
        conn.commit()
    conn.close()


def test_booking_staff_cannot_access_admin_dashboard(client):
    seed_staff_user()  # ✅ Seed user into test DB

    login_response = client.post('/staff_login', data={
        "username": "staff1",
        "password": "Staff!Pass789"
    }, follow_redirects=True)

    assert login_response.status_code == 200
    assert b"booking" in login_response.data.lower()

    # ✅ Correct route
    response = client.get('/admin_dashboard')

    # ✅ Staff should NOT have access
    assert response.status_code in [302, 401, 403]