import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect("horizon_cinemas.db")
    conn.row_factory = sqlite3.Row
    return conn

def generate_booking_charts():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 🎟 Bookings by Showtime
        cursor.execute("""
            SELECT showtimes.show_time, COUNT(bookings.id) AS total_bookings
            FROM bookings
            JOIN showtimes ON bookings.showtime_id = showtimes.id
            GROUP BY showtimes.show_time
        """)
        df_showtimes = pd.DataFrame(cursor.fetchall(), columns=["show_time", "total_bookings"])
        
        plt.figure(figsize=(8, 4))
        plt.bar(df_showtimes["show_time"], df_showtimes["total_bookings"], color="blue")
        plt.xlabel("Showtime")
        plt.ylabel("Total Bookings")
        plt.title("Bookings by Showtime")
        plt.xticks(rotation=45)
        plt.savefig("static/charts/showtime_bookings.png")
        plt.close()

        # 🏙 Bookings by City
        cursor.execute("""
            SELECT cinemas.city, COUNT(bookings.id) AS total_bookings
            FROM bookings
            JOIN showtimes ON bookings.showtime_id = showtimes.id
            JOIN cinemas ON showtimes.cinema_id = cinemas.id
            GROUP BY cinemas.city
        """)
        df_cities = pd.DataFrame(cursor.fetchall(), columns=["city", "total_bookings"])

        plt.figure(figsize=(6, 4))
        plt.pie(df_cities["total_bookings"], labels=df_cities["city"], autopct="%1.1f%%", startangle=140)
        plt.title("Bookings by City")
        plt.savefig("static/charts/city_bookings.png")
        plt.close()

if __name__ == "__main__":
    generate_booking_charts()