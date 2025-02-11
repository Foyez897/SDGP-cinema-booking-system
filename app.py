from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import traceback
from datetime import datetime, timedelta
from database_setup import get_db_connection
import uuid
import sqlite3



app = Flask(__name__)
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# 🔹 Configure JWT
app.config["JWT_SECRET_KEY"] = "supersecurejwtkey"  # Change this to a secure key
jwt = JWTManager(app)
# ===============================
# 🔹 Serve the Home Page
# ===============================
@app.route('/')
def home():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT films.id, films.title, films.genre, films.age_rating, films.description,
                   GROUP_CONCAT(showtimes.show_time) AS showtimes
            FROM films
            LEFT JOIN showtimes ON films.id = showtimes.film_id
            GROUP BY films.id
        """)
        films = cursor.fetchall()

    return render_template("index.html", films=films)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid username or password"}), 401

        access_token = create_access_token(identity={"username": username, "role": user["role"]})
        return jsonify({"message": "✅ Login successful", "access_token": access_token})
# ===============================
# 🔹 Film Listings (NEW)
# ===============================
@app.route('/films', methods=['GET'])
def get_films():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM films")
        films = cursor.fetchall()

    film_list = [dict(film) for film in films]
    return jsonify(film_list)

# ===============================
# 🔹 Admin: Add New Film (NEW)
# ===============================
@app.route('/admin/add_film', methods=['POST'])
def add_film():
    data = request.get_json()
    title = data.get("title")
    genre = data.get("genre")
    age_rating = data.get("age_rating")
    description = data.get("description")
    actors = data.get("actors")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO films (title, genre, age_rating, description, actors) VALUES (?, ?, ?, ?, ?)",
                       (title, genre, age_rating, description, actors))
        conn.commit()

    return jsonify({"message": "✅ Film added successfully!"}), 201

@app.route('/admin_dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user = get_jwt_identity()
    if current_user["role"] != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({"message": f"Welcome, {current_user['username']}! This is the Admin Dashboard."})


@app.route('/manager_dashboard', methods=['GET'])
@jwt_required()
def manager_dashboard():
    current_user = get_jwt_identity()
    if current_user["role"] not in ["manager", "admin"]:  # Managers & Admins can access
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({"message": f"Welcome, {current_user['username']}! This is the Manager Dashboard."})

@app.route('/manager_dashboard')
def manager_dashboard():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch booking summary per cinema
        cursor.execute("""
            SELECT cinemas.city, COUNT(bookings.id) AS total_bookings, SUM(bookings.total_price) AS total_revenue
            FROM bookings
            JOIN showtimes ON bookings.showtime_id = showtimes.id
            JOIN cinemas ON showtimes.cinema_id = cinemas.id
            GROUP BY cinemas.city
        """)
        booking_summary = cursor.fetchall()

    return render_template("manager_dashboard.html", booking_summary=booking_summary)

# ===============================
# 🔹 Get Available Seats
# ===============================
@app.route('/seats/<int:showtime_id>', methods=['GET'])
def get_available_seats(showtime_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, seat_number, seat_type, price FROM seats WHERE showtime_id = ? AND is_booked = 0", (showtime_id,))
        seats = cursor.fetchall()

    return jsonify([dict(seat) for seat in seats])

# ===============================
# 🔹 Calculate Pricing Based on City & Seat Type (NEW)
# ===============================
def calculate_price(city, seat_type, base_price):
    city_prices = {
        "Birmingham": [5, 6, 7],
        "Bristol": [6, 7, 8],
        "Cardiff": [5, 6, 7],
        "London": [10, 11, 12]
    }

    # Apply price based on city
    time_now = datetime.now().hour
    if 8 <= time_now < 12:
        price = city_prices[city][0]
    elif 12 <= time_now < 17:
        price = city_prices[city][1]
    else:
        price = city_prices[city][2]

    # Apply seat type pricing
    if seat_type == "upper_gallery":
        price *= 1.2
    elif seat_type == "vip":
        price = (price + (price * 0.2)) * 1.2

    return round(price, 2)

# ===============================
# 🔹 Book a Seat
# ===============================
@app.route('/book', methods=['POST'])
@jwt_required()
def book_ticket():
    current_user = get_jwt_identity()
    if current_user["role"] not in ["admin", "manager", "booking_staff"]:
        return jsonify({"error": "Unauthorized!"}), 403

    data = request.get_json()
    customer_name = data.get("customer_name")
    customer_email = data.get("customer_email")
    customer_phone = data.get("customer_phone")
    showtime_id = data.get("showtime_id")
    seat_ids = data.get("seat_ids")

    if not seat_ids:
        return jsonify({"error": "Please select at least one seat."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check seat availability
        placeholders = ",".join("?" * len(seat_ids))
        cursor.execute(f"SELECT id FROM seats WHERE id IN ({placeholders}) AND is_booked = 0", seat_ids)
        available_seats = cursor.fetchall()

        if len(available_seats) != len(seat_ids):
            return jsonify({"error": "One or more selected seats are already booked!"}), 400

        # Calculate total price
        cursor.execute("SELECT price FROM showtimes WHERE id = ?", (showtime_id,))
        price_per_ticket = cursor.fetchone()["price"]
        total_price = len(seat_ids) * price_per_ticket

        # Generate booking reference
        booking_reference = str(uuid.uuid4())[:8]

        # Insert booking records
        for seat_id in seat_ids:
            cursor.execute("""
                INSERT INTO bookings (customer_name, customer_email, customer_phone, showtime_id, seat_id, booking_reference, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (customer_name, customer_email, customer_phone, showtime_id, seat_id, booking_reference, total_price))
            cursor.execute("UPDATE seats SET is_booked = 1 WHERE id = ?", (seat_id,))

        conn.commit()

    return jsonify({"message": "✅ Booking successful!", "booking_reference": booking_reference, "total_price": total_price}), 201

@app.route('/check_cancellation/<booking_reference>', methods=['GET'])
def check_cancellation(booking_reference):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch booking details
        cursor.execute("SELECT id, showtime_id, total_price FROM bookings WHERE booking_reference = ?", (booking_reference,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Invalid booking reference!"}), 400

        # Get the showtime date
        cursor.execute("SELECT show_time FROM showtimes WHERE id = ?", (booking["showtime_id"],))
        showtime = cursor.fetchone()

        if not showtime:
            return jsonify({"error": "Showtime not found!"}), 400

        showtime_date = datetime.strptime(showtime["show_time"], '%Y-%m-%d %H:%M:%S')

        # Check cancellation rules
        today = datetime.now()
        if showtime_date.date() == today.date():
            return jsonify({"error": "Cancellation is not allowed on the day of the show!"}), 400

        refund_amount = round(booking["total_price"] * 0.5, 2)  # 50% refund
        return jsonify({"message": "Cancellation allowed.", "refund_amount": refund_amount})
@app.route('/cancel_booking', methods=['POST'])


@app.route('/cancel_booking', methods=['POST'])
@jwt_required()
def cancel_booking():
    current_user = get_jwt_identity()
    booking_reference = request.json.get("booking_reference")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch booking
        cursor.execute("SELECT id, showtime_id, total_price FROM bookings WHERE booking_reference = ?", (booking_reference,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Invalid booking reference!"}), 400

        # Get the showtime date
        cursor.execute("SELECT show_time FROM showtimes WHERE id = ?", (booking["showtime_id"],))
        showtime = cursor.fetchone()
        showtime_date = datetime.strptime(showtime["show_time"], '%Y-%m-%d %H:%M:%S')

        # Check cancellation rules
        today = datetime.now()
        if showtime_date.date() == today.date():
            return jsonify({"error": "Cancellation is not allowed on the day of the show!"}), 400

        refund_amount = round(booking["total_price"] * 0.5, 2)  # 50% refund

        # Insert cancellation record
        cursor.execute("INSERT INTO cancellations (booking_id, cancellation_date, refund_amount) VALUES (?, ?, ?)",
                       (booking["id"], today.strftime('%Y-%m-%d'), refund_amount))
        
        # Delete booking
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        cursor.execute("UPDATE seats SET is_booked = 0 WHERE id = (SELECT seat_id FROM bookings WHERE id = ?)", (booking["id"],))

        conn.commit()

    return jsonify({"message": "✅ Booking cancelled successfully!", "refund_amount": refund_amount}), 200
# ===============================
# 🔹 Run Flask App
# ===============================
if __name__ == "__main__":
    app.run(debug=True, port=5003)