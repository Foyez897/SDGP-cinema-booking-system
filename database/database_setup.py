import os
import sqlite3
from flask import current_app

def get_db_connection(testing=False):
    try:
        # Use Flask config if inside app context
        testing = current_app.config.get("TESTING", False)
    except RuntimeError:
        # Use passed parameter if no app context
        pass

    db_name = 'horizon_cinemas_test.db' if testing else 'horizon_cinemas.db'
    db_path = os.path.join(os.path.dirname(__file__), db_name)

    print("✅ get_db_connection() called")
    print(f"📍 USING DB: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(testing=False):
    # Use correct database path even when run directly
    db_name = 'horizon_cinemas_test.db' if testing else 'horizon_cinemas.db'
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK (role IN ('admin', 'manager', 'booking_staff')) NOT NULL
        );
    ''')

    # Cinemas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cinemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            location TEXT NOT NULL,
            num_of_screens INTEGER NOT NULL
        );
    ''')

    # Screens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cinema_id INTEGER NOT NULL,
            screen_number INTEGER NOT NULL,
            total_seats INTEGER NOT NULL CHECK (total_seats BETWEEN 50 AND 120),
            FOREIGN KEY (cinema_id) REFERENCES cinemas(id) ON DELETE CASCADE
        );
    ''')

    # Films
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            age_rating TEXT NOT NULL,
            description TEXT,
            actors TEXT
        );
    ''')

    # Showtimes (MATCHED to production)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER NOT NULL,
            cinema_id INTEGER NOT NULL,
            screen_number INTEGER NOT NULL,
            show_time TEXT NOT NULL,
            price INTEGER NOT NULL
        );
    ''')

    # Seats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            screen_id INTEGER NOT NULL,
            seat_number INTEGER NOT NULL,
            seat_type TEXT NOT NULL,
            is_booked INTEGER DEFAULT 0,
            FOREIGN KEY(screen_id) REFERENCES screens(id)
        );
    ''')

    # Bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            showtime_id INTEGER,
            seat_id INTEGER,
            booking_reference TEXT,
            total_price REAL,
            booking_staff_id INTEGER,
            booking_date TEXT,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id),
            FOREIGN KEY (seat_id) REFERENCES seats(id),
            FOREIGN KEY (booking_staff_id) REFERENCES users(id)
        );
    ''')

    # Cancellations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cancellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            cancellation_date TEXT NOT NULL,
            refund_amount REAL NOT NULL,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        );
    ''')

    # Pricing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            time_slot TEXT CHECK (time_slot IN ('morning', 'afternoon', 'evening')) NOT NULL,
            lower_hall_price REAL NOT NULL
        );
    ''')

    conn.commit()
    conn.close()
    print("✅ Database Initialized Successfully!")


if __name__ == "__main__":
    # You can pass testing=True here manually if needed
    initialize_database()