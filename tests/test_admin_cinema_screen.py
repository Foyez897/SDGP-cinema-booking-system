from tests.test_helpers import seed_admin_user
from database.database_setup import get_db_connection

def test_add_cinema_and_screens(client):
    seed_admin_user()

    # Log in as admin
    login_response = client.post('/admin_login', data={
        "username": "admin1",
        "password": "Admin123Pass_"
    }, follow_redirects=True)
    assert login_response.status_code == 200

    # Submit the add cinema form
    response = client.post('/add_cinema', data={
        "cinema_name": "Test Cinema",
        "city": "Testville",
        "address": "123 Test Street",
        "num_of_screens": 2,   # Matches allowed values
        "seat_config_1": "80",
        "seat_config_2": "100",
        "vip_percentage": 10  # optional if your form uses it
    }, follow_redirects=True)

    assert response.status_code in [200, 302]

    # Check if cinema was added to DB
    with get_db_connection(testing=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cinemas WHERE city = ?", ("Testville",))
        cinema = cursor.fetchone()
        assert cinema is not None