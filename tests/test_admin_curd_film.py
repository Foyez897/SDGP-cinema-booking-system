from tests.test_helpers import seed_cinema_and_screen, seed_admin_user
from database.database_setup import get_db_connection

def test_admin_can_add_film_and_showtime(client):
    seed_admin_user()
    cinema_id, screen_number = seed_cinema_and_screen()

    # Login
    login_response = client.post('/admin_login', data={
        "username": "admin1",
        "password": "Admin123Pass_"
    }, follow_redirects=True)
    assert login_response.status_code == 200

    # Add film
    response = client.post('/add_film', data={
        "title": "Matrix",
        "genre": "Sci-Fi",
        "age_rating": "PG-13",
        "description": "Test description",
        "cinema_id": cinema_id,
        "price": 12.0,
        "showtimes[]": ["2025-04-05 18:00:00"],
        "screens[]": [str(screen_number)]
    }, follow_redirects=True)

    assert response.status_code in [200, 302]

    # Optional DB check
    with get_db_connection(testing=True) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM films WHERE title = ?", ("Matrix",))
        assert cursor.fetchone() is not None