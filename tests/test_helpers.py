import bcrypt
from tests.test_helpers import seed_admin_user
from database.database_setup import get_db_connection
from app import create_app, db

def seed_cinema_and_screen():
    conn = get_db_connection(testing=True)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO cinemas (city, location, num_of_screens) VALUES (?, ?, ?)",
                   ("TestCity", "TestLocation", 1))
    cinema_id = cursor.lastrowid

    cursor.execute("INSERT INTO screens (cinema_id, screen_number, total_seats) VALUES (?, ?, ?)",
                   (cinema_id, 1, 100))

    conn.commit()
    conn.close()

    return cinema_id, 1  # returning screen_number as 1


from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def seed_staff_user():
    conn = get_db_connection(testing=True)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE username = ?", ("staff1",))
    hashed_pw = bcrypt.generate_password_hash("Staff!Pass789").decode("utf-8")

    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("staff1", hashed_pw, "booking_staff"))

    conn.commit()
    conn.close()


def seed_test_db():
    conn = get_db_connection(testing=True)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS cinemas (
        id INTEGER PRIMARY KEY,
        city TEXT,
        location TEXT,
        num_of_screens INTEGER
    );
    CREATE TABLE IF NOT EXISTS screens (
        id INTEGER PRIMARY KEY,
        cinema_id INTEGER,
        screen_number INTEGER,
        total_seats INTEGER
    );
    CREATE TABLE IF NOT EXISTS films (
        id INTEGER PRIMARY KEY,
        title TEXT,
        genre TEXT,
        age_rating TEXT,
        description TEXT,
        actors TEXT
    );
    CREATE TABLE IF NOT EXISTS showtimes (
        id INTEGER PRIMARY KEY,
        film_id INTEGER,
        cinema_id INTEGER,
        screen_number INTEGER,
        show_time TEXT,
        price INTEGER
    );
    CREATE TABLE IF NOT EXISTS seats (
        id INTEGER PRIMARY KEY,
        screen_id INTEGER,
        seat_number INTEGER,
        seat_type TEXT,
        is_booked INTEGER DEFAULT 0
    );
    """)

    cursor.execute("INSERT INTO cinemas (city, location, num_of_screens) VALUES (?, ?, ?)",
                   ("Test City", "Test Location", 1))
    cinema_id = cursor.lastrowid

    cursor.execute("INSERT INTO screens (cinema_id, screen_number, total_seats) VALUES (?, ?, ?)",
                   (cinema_id, 1, 100))
    screen_id = cursor.lastrowid

    cursor.execute("INSERT INTO films (title, genre, age_rating, description, actors) VALUES (?, ?, ?, ?, ?)",
                   ("Test Film", "Drama", "PG", "A test film", "Actor A, Actor B"))
    film_id = cursor.lastrowid

    cursor.execute("INSERT INTO showtimes (film_id, cinema_id, screen_number, show_time, price) VALUES (?, ?, ?, ?, ?)",
                   (film_id, cinema_id, 1, "2025-04-10 19:00:00", 100))
    showtime_id = cursor.lastrowid

    cursor.execute("INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, ?, ?)",
                   (screen_id, 1, "Lower Hall"))
    seat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return showtime_id, seat_id