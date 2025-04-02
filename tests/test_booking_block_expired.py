from test_helpers import seed_past_showtime
import pytest
from tests.test_helpers import seed_past_showtime
from database.database_setup import get_db_connection
from datetime import datetime, timedelta
import bcrypt

def seed_staff_user():
    conn = get_db_connection(testing=True)
    cursor = conn.cursor()

    # Delete any duplicate
    cursor.execute("DELETE FROM users WHERE username = ?", ("staff1",))

    hashed_pw = bcrypt.hashpw("Staff!Pass789".encode("utf-8"), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("staff1", hashed_pw.decode("utf-8"), "booking_staff"))


    
    cursor.execute("INSERT INTO cinemas (city, location, num_of_screens) VALUES (?, ?, ?)",
                   ("TestCity", "TestLocation", 1))
    cinema_id = cursor.lastrowid

    cursor.execute("INSERT INTO screens (cinema_id, screen_number, total_seats) VALUES (?, ?, ?)",
                   (cinema_id, 1, 100))
    screen_id = cursor.lastrowid

    cursor.execute("INSERT INTO films (title, genre, age_rating) VALUES (?, ?, ?)",
                   ("Expired Film", "Drama", "PG"))
    film_id = cursor.lastrowid

    expired_showtime = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO showtimes (film_id, cinema_id, screen_number, show_time, price) VALUES (?, ?, ?, ?, ?)",
                   (film_id, cinema_id, 1, expired_showtime, 10))
    showtime_id = cursor.lastrowid

    cursor.execute("INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, ?, ?)",
                   (screen_id, 1, "Lower Hall"))
    seat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return showtime_id, seat_id


@pytest.fixture
def setup_test_db():
    return seed_past_showtime()


def test_block_expired_showtime_booking(client, setup_test_db):
    showtime_id, seat_id = setup_test_db

    response = client.post('/book', json={
        "showtime_id": showtime_id,
        "customer_name": "Expired Test",
        "customer_email": "expired@test.com",
        "customer_phone": "0000000000",
        "seat_ids": [str(seat_id)]
    })

    assert response.status_code == 400
    assert b"Cannot book past showtimes" in response.data