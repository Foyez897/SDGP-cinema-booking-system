from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies
import traceback
from datetime import datetime, timedelta
from database_setup import get_db_connection
import uuid
import numpy as np
from sklearn.linear_model import LinearRegression
import sqlite3
import re
from flask_jwt_extended import get_jwt

app = Flask(__name__)
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# 🔹 Configure JWT
# ✅ Enforce HTTPS for JWT
app.config["JWT_COOKIE_SECURE"] = True  # Requires HTTPS
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ✅ Set JWT Expiry to 30 minutes for testing
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
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

# ===============================
# 🔹 Admin Login
# ===============================

def is_strong_password(password):
    """Ensure password is strong: At least 8 chars, contains numbers & symbols."""
    return bool(re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.form if not request.is_json else request.get_json()
        username = data.get("username")
        password = data.get("password")

        # ✅ Validate Password
        if not is_strong_password(password):
            flash("❌ Password must be at least 8 characters, include numbers & symbols.", "danger")
            return redirect(url_for('admin_login'))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user["password"], password):
            flash("Invalid username or password", "danger")
            return redirect(url_for('admin_login'))

        # ✅ Generate JWT token
        access_token = create_access_token(identity=str(user["id"]))

        # ✅ Create response and set JWT in **httpOnly cookie**
        response = make_response(redirect(url_for('admin_dashboard')))
        set_access_cookies(response, access_token)

        flash("✅ Login successful!", "success")
        return response

    return render_template('admin_login.html')

# ===============================
# 🔹 Admin Dashboard
# ===============================
@app.route('/admin_dashboard', methods=['GET'])
@jwt_required(locations=["headers", "cookies"])
def admin_dashboard():
    user_id = get_jwt_identity()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

    if not user or user["role"] != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    # 🔹 Auto-logout if session expired
    exp_timestamp = get_jwt()["exp"]
    if datetime.fromtimestamp(exp_timestamp) < datetime.utcnow():
        return jsonify({"error": "Session expired, please log in again."}), 401

    return jsonify({"message": f"Welcome, Admin {user_id}!"})

# ===============================
# 🔹 Manager Login
# ===============================
def is_strong_password(password):
    """Ensure password is strong: At least 8 chars, contains numbers & symbols."""
    return bool(re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password))

@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        data = request.form if not request.is_json else request.get_json()
        username = data.get("username")
        password = data.get("password")

        # ✅ Validate Password
        if not is_strong_password(password):
            flash("❌ Password must be at least 8 characters, include numbers & symbols.", "danger")
            return redirect(url_for('manager_login'))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user["password"], password):
            flash("Invalid username or password", "danger")
            return redirect(url_for('manager_login'))

        # ✅ Generate JWT token
        access_token = create_access_token(identity=str(user["id"]))

        # ✅ Create response and set JWT in **httpOnly cookie**
        response = make_response(redirect(url_for('manager_dashboard')))
        set_access_cookies(response, access_token)

        flash("✅ Manager Login successful!", "success")
        return response

    return render_template('manager_login.html')
# ===============================
# 🔹 Manager Dashboard
# ===============================
@app.route('/manager_dashboard', methods=['GET'])
@jwt_required(locations=["headers", "cookies"])
def manager_dashboard():
    user_id = get_jwt_identity()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

    if not user or user["role"] not in ["manager", "admin"]:
        return jsonify({"error": "Unauthorized access"}), 403

    cursor.execute("""
        SELECT cinemas.city, COUNT(bookings.id) AS total_bookings, SUM(bookings.total_price) AS total_revenue
        FROM bookings
        JOIN showtimes ON bookings.showtime_id = showtimes.id
        JOIN cinemas ON showtimes.cinema_id = cinemas.id
        GROUP BY cinemas.city
    """)

    # ✅ Convert each Row object to a dictionary
    booking_summary = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        "message": f"Welcome, {user['role']}!",
        "booking_summary": booking_summary
    })

# ===============================
# 🔹 Booking: Check Booking Validity (Max 7 Days in Advance)
# ===============================
@app.route('/book', methods=['POST'])
@jwt_required()
def book_ticket():
    user_id = get_jwt_identity()
    data = request.get_json()

    showtime_id = data.get("showtime_id")
    customer_name = data.get("customer_name")
    customer_email = data.get("customer_email")
    customer_phone = data.get("customer_phone")
    seat_ids = data.get("seat_ids")

    if not all([customer_name, customer_email, customer_phone, showtime_id, seat_ids]):
        return jsonify({"error": "Missing required booking details."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get showtime date
        cursor.execute("SELECT show_time FROM showtimes WHERE id = ?", (showtime_id,))
        showtime_data = cursor.fetchone()
        if not showtime_data:
            return jsonify({"error": "Invalid Showtime!"}), 400

        showtime_date = datetime.strptime(showtime_data["show_time"], "%Y-%m-%d %H:%M:%S")

        # ✅ Check if booking is within 7 days
        if showtime_date > datetime.now() + timedelta(days=7):
            return jsonify({"error": "❌ Tickets can only be booked 7 days in advance!"}), 400

        # ✅ Process each seat
        placeholders = ",".join("?" * len(seat_ids))
        cursor.execute(f"SELECT id FROM seats WHERE id IN ({placeholders}) AND is_booked = 0", seat_ids)
        available_seats = cursor.fetchall()

        if len(available_seats) != len(seat_ids):
            return jsonify({"error": "One or more selected seats are already booked!"}), 400

        total_price = 0  # Initialize total price

        for seat_id in seat_ids:
            seat_reference = str(uuid.uuid4())[:8]

            cursor.execute("SELECT price FROM seats WHERE id = ?", (seat_id,))
            seat_price = cursor.fetchone()["price"]
            total_price += seat_price

            cursor.execute("""
                INSERT INTO bookings (customer_name, customer_email, customer_phone, showtime_id, seat_id, 
                                      booking_reference, total_price, booking_staff_id, booking_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_name, customer_email, customer_phone, showtime_id, seat_id,
                  seat_reference, seat_price, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            cursor.execute("UPDATE seats SET is_booked = 1 WHERE id = ?", (seat_id,))

        conn.commit()

    return jsonify({
        "message": "✅ Booking successful!",
        "total_price": total_price
    }), 201

# ===============================
# 🔹 Cancellation Policy: 50% Refund (At Least 1 Day Before Show)
# ===============================
@app.route('/cancel_booking', methods=['POST'])
@jwt_required()
def cancel_booking():
    user_id = get_jwt_identity()
    booking_reference = request.json["booking_reference"]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, showtime_id, total_price FROM bookings WHERE booking_reference = ?", 
                       (booking_reference,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Invalid booking reference!"}), 400

        # Get showtime date
        cursor.execute("SELECT show_time FROM showtimes WHERE id = ?", (booking["showtime_id"],))
        showtime_date = datetime.strptime(cursor.fetchone()["show_time"], "%Y-%m-%d %H:%M:%S")

        if (showtime_date - datetime.now()).days < 1:
            return jsonify({"error": "❌ Cannot cancel on the day of the show!"}), 403

        refund_amount = booking["total_price"] * 0.5  # 50% refund

        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        conn.commit()

    return jsonify({"message": f"✅ Booking cancelled! Refund Amount: £{refund_amount:.2f}"}), 200

# ===============================
# 🔹 AI Model: Predict Future Booking Demand
# ===============================
@app.route('/predict_bookings', methods=['GET'])
def predict_bookings():
    # Example dataset (replace with real booking history)
    time_slots = np.array([10, 14, 18, 21]).reshape(-1, 1)
    bookings = np.array([50, 80, 120, 100])  # Example number of bookings

    model = LinearRegression()
    model.fit(time_slots, bookings)

    # Predict bookings for 8 PM (20:00)
    predicted_bookings = model.predict(np.array([[20]]))

    return jsonify({"predicted_bookings_for_8PM": int(predicted_bookings[0])})


from flask_jwt_extended import unset_jwt_cookies

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = make_response(jsonify({"message": "✅ Logged out successfully!"}))
    unset_jwt_cookies(response)  # Remove JWT from cookies
    return response

# ===============================
# 🔹 Run Flask App
# ===============================
if __name__ == "__main__":
    app.run(debug=True, port=5003)