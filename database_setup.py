import sqlite3

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect("horizon_cinemas.db")
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access to rows
    return conn

def initialize_database():
    """Creates required tables for the Horizon Cinemas Booking System."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table (Admins, Managers, Booking Staff)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'manager', 'booking_staff')) NOT NULL
        )
    ''')

    # Cinemas Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cinemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            location TEXT NOT NULL,
            num_of_screens INTEGER NOT NULL
        )
    ''')

    # Films Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            age_rating TEXT NOT NULL,
            description TEXT,
            actors TEXT
        )
    ''')

    # Showtimes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER NOT NULL,
            cinema_id INTEGER NOT NULL,
            screen_number INTEGER NOT NULL,
            show_time TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (film_id) REFERENCES films(id),
            FOREIGN KEY (cinema_id) REFERENCES cinemas(id)
        )
    ''')

    # Seats Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER NOT NULL,
            seat_number INTEGER NOT NULL,
            seat_type TEXT NOT NULL CHECK(seat_type IN ('lower_hall', 'upper_gallery', 'vip')),
            is_booked INTEGER DEFAULT 0,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
        )
    ''')

    # Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_staff_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            showtime_id INTEGER NOT NULL,
            seat_id INTEGER NOT NULL,
            booking_reference TEXT UNIQUE NOT NULL,
            total_price REAL NOT NULL,
            booking_date TEXT NOT NULL,
            FOREIGN KEY (booking_staff_id) REFERENCES users(id),
            FOREIGN KEY (seat_id) REFERENCES seats(id)
        )
    ''')

    # Cancellations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cancellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            cancellation_date TEXT NOT NULL,
            refund_amount REAL NOT NULL,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database Initialized Successfully!")

if __name__ == "__main__":
    initialize_database()