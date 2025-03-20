from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, flash, make_response
)
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies, unset_jwt_cookies, get_jwt
)
import traceback
from datetime import datetime, timedelta, UTC
from database_setup import get_db_connection
import uuid
import numpy as np
from sklearn.linear_model import LinearRegression
import re
import logging
from flask_bcrypt import check_password_hash

# 🔹 Initialize Flask App
app = Flask(__name__)
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# 🔹 Configure JWT
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False  # Set to True for production with HTTPS
app.config["JWT_COOKIE_HTTPONLY"] = True
app.config["JWT_COOKIE_SAMESITE"] = "Lax"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Disable CSRF for JWT in cookies
jwt = JWTManager(app)

# 🔹 Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ===============================
# 🔹 Utility Functions
# ===============================

def is_strong_password(password):
    """Ensure password has at least 8 characters, including numbers & symbols."""
    return bool(re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password))

# Disable CSRF protection for API routes
@app.before_request
def disable_csrf():
    exempt_endpoints = ["book_ticket"]
    if request.endpoint in exempt_endpoints:
        request.csrf_valid = True

# ===============================
# 🔹 Serve Home Page
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
# 🔹 Booking Staff Login
# ===============================
@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'GET':
        return render_template('staff_login.html')  # Ensure this HTML file exists

    data = request.get_json() if request.is_json else request.form
    username = data.get("username")
    password = data.get("password")

    logging.info(f"DEBUG: Logging in staff: {username}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(user[1], password):
        logging.warning("DEBUG: Invalid username or password")
        return render_template('staff_login.html', error="Invalid username or password")  # Render login page with error

    # Generate JWT token
    access_token = create_access_token(identity=str(user[0]))
    
    response = make_response(redirect(url_for('booking_page')))  # ✅ Redirect to booking page
    set_access_cookies(response, access_token)

    logging.info(f"DEBUG: JWT token set for {username}")
    return response  # ✅ Redirects to 'booking.html' instead of returning JSON

# ===============================
# 🔹 Booking Page (New Route)
# ===============================
@app.route('/booking')
@jwt_required()
def booking_page():
    """Renders the booking.html page for staff after login."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # ✅ Fetch showtimes
        cursor.execute("SELECT id, show_time, price FROM showtimes")
        showtimes = cursor.fetchall()

        # ✅ Fetch available films
        cursor.execute("SELECT id, title, genre, age_rating FROM films")
        films = cursor.fetchall()

        # ✅ Fetch available seats
        cursor.execute("SELECT id, seat_number, seat_type FROM seats WHERE is_booked = 0")
        seats = cursor.fetchall()

    return render_template(
        "booking.html",
        showtimes=showtimes, 
        films=films,
        seats=seats
    )

# ===============================
# 🔹 Book Ticket API (Protected)
# ===============================
@app.route('/book', methods=['POST'])
@jwt_required(locations=["headers", "cookies"])
def book_ticket():
    user_id = get_jwt_identity()

    # 🔍 Debugging: Print incoming request details
    print("DEBUG: Request Headers:", request.headers)
    print("DEBUG: Request Content-Type:", request.content_type)
    print("DEBUG: Raw Request Data:", request.data.decode("utf-8"))

    # ✅ Handle both JSON & Form Data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    showtime_id = data.get("showtime_id")
    customer_name = data.get("customer_name")
    customer_email = data.get("customer_email")
    customer_phone = data.get("customer_phone")
    seat_ids = data.get("seat_ids")

    if not all([customer_name, customer_email, customer_phone, showtime_id, seat_ids]):
        return jsonify({"error": "Missing required booking details."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ✅ Fetch showtime
        cursor.execute("SELECT show_time FROM showtimes WHERE id = ?", (showtime_id,))
        showtime_data = cursor.fetchone()

        if not showtime_data:
            return jsonify({"error": "Invalid Showtime!"}), 400

        showtime_date = datetime.strptime(showtime_data[0], "%Y-%m-%d %H:%M:%S")

        # ✅ Allow booking only within 7 days
        if showtime_date > datetime.now() + timedelta(days=7):
            return jsonify({"error": "❌ Tickets can only be booked 7 days in advance!"}), 400

        # ✅ Ensure seats are available
        if isinstance(seat_ids, str):  
            seat_ids = seat_ids.split(",")  # Handle form data case

        placeholders = ",".join("?" * len(seat_ids))
        cursor.execute(f"SELECT id FROM seats WHERE id IN ({placeholders}) AND is_booked = 0", seat_ids)
        available_seats = cursor.fetchall()

        if len(available_seats) != len(seat_ids):
            return jsonify({"error": "One or more selected seats are already booked!"}), 400

        total_price = 0
        for seat_id in seat_ids:
            seat_reference = str(uuid.uuid4())[:8]
            cursor.execute("SELECT price FROM seats WHERE id = ?", (seat_id,))
            seat_price = cursor.fetchone()[0]  # ✅ Use tuple indexing
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
# 🔹 AI Model: Predict Future Booking Demand
# ===============================
@app.route('/predict_bookings', methods=['GET'])
def predict_bookings():
    time_slots = np.array([10, 14, 18, 21]).reshape(-1, 1)
    bookings = np.array([50, 80, 120, 100])

    model = LinearRegression()
    model.fit(time_slots, bookings)

    predicted_bookings = model.predict(np.array([[20]]))
    return jsonify({"predicted_bookings_for_8PM": int(predicted_bookings[0])})

# ===============================
# 🔹 Admin Login 
# ===============================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            if user["role"] not in ["admin", "manager"]:
                flash("❌ Unauthorized access!", "danger")
                return redirect(url_for('admin_login'))

            access_token = create_access_token(identity=str(user["id"]))  # ✅ Convert user ID to string
            resp = make_response(redirect(url_for("admin_dashboard")))
            set_access_cookies(resp, access_token)  # ✅ This ensures JWT is stored correctly
            return resp

        flash("❌ Invalid username or password!", "danger")

    return render_template("admin_login.html")

# ===============================
# 🔹 Admin Dashboard (Now Renders admin_dashboard.html)
# ===============================
@app.route('/admin_dashboard', methods=['GET'])
@jwt_required(locations=["cookies"])  # ✅ Ensure JWT is read from cookies
def admin_dashboard():
    user_id = get_jwt_identity()
    print(f"DEBUG: Admin Dashboard Access - User ID: {user_id}")  # Debugging

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("❌ Please log in first!", "danger")
            return redirect(url_for('admin_login'))

        if user["role"] not in ["admin", "manager"]:
            flash("❌ Unauthorized access!", "danger")
            return redirect(url_for('home'))  # Redirect to home instead of login

        # Fetch films for admin management
        cursor.execute("""
            SELECT films.id, films.title, films.genre, films.age_rating,
                   GROUP_CONCAT(DISTINCT showtimes.show_time) AS showtimes
            FROM films
            LEFT JOIN showtimes ON films.id = showtimes.film_id
            GROUP BY films.id
        """)
        films = cursor.fetchall()

    return render_template("admin_dashboard.html", admin_id=user_id, films=films)
# ===============================
# 🔹 Add Film Route
# ===============================
@app.route('/add_film', methods=['GET', 'POST'])
@jwt_required()
def add_film():
    if request.method == 'GET':
        return render_template("add_film.html")  # Make sure this file exists in 'templates/'

    data = request.form
    title, genre, age_rating = data["title"], data["genre"], data["age_rating"]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO films (title, genre, age_rating) VALUES (?, ?, ?)",
                       (title, genre, age_rating))
        conn.commit()

    flash("✅ Film added successfully!", "success")
    return redirect(url_for('admin_dashboard'))
# ===============================
# 🔹 Update Film Route
# ===============================
@app.route('/update_film/<int:film_id>', methods=['GET', 'POST'])
@jwt_required()
def update_film(film_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute("SELECT * FROM films WHERE id = ?", (film_id,))
            film = cursor.fetchone()
            return render_template("update_film.html", film=film)

        data = request.form
        title, genre, age_rating = data["title"], data["genre"], data["age_rating"]

        cursor.execute("UPDATE films SET title = ?, genre = ?, age_rating = ? WHERE id = ?",
                       (title, genre, age_rating, film_id))
        conn.commit()

    flash("✅ Film updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ===============================
# 🔹 Remove Film Route
# ===============================
@app.route('/delete_film/<int:film_id>', methods=['GET'])
@jwt_required()
def delete_film(film_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM films WHERE id = ?", (film_id,))
        conn.commit()

    flash("✅ Film removed successfully!", "success")
    return redirect(url_for('admin_dashboard'))
# ===============================
# 🔹 Route for Generating Reports
# ===============================
@app.route('/report/bookings_per_film')
@jwt_required()
def bookings_per_film():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT films.title, COUNT(bookings.id) AS total_bookings 
            FROM films 
            LEFT JOIN showtimes ON films.id = showtimes.film_id 
            LEFT JOIN bookings ON showtimes.id = bookings.showtime_id 
            GROUP BY films.title 
            ORDER BY total_bookings DESC;
        """)
        report = cursor.fetchall()
    return render_template("report.html", report=report, title="Bookings Per Film")

@app.route('/report/monthly_revenue')
@jwt_required()
def monthly_revenue():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Extract month and year from booking_date and sum total_price
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', booking_date) AS month,
                SUM(total_price) AS total_revenue
            FROM bookings
            GROUP BY strftime('%Y-%m', booking_date)
            ORDER BY month DESC
        """)
        
        report = cursor.fetchall()
        
        # Define columns for the report
        columns = [
            {"key": "month", "display_name": "Month", "format": "text"},
            {"key": "total_revenue", "display_name": "Total Revenue", "format": "currency"}
        ]
        
    return render_template(
        "generic_report.html", 
        report=report, 
        columns=columns,
        title="Monthly Revenue Report"
    )

@app.route('/report/top_film')
@jwt_required()
def top_film():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                f.title, 
                SUM(b.total_price) AS total_revenue,
                COUNT(b.id) AS booking_count,
                f.genre,
                f.age_rating
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.id
            JOIN films f ON s.film_id = f.id
            GROUP BY f.title, f.genre, f.age_rating
            ORDER BY total_revenue DESC
        """)
        
        report = cursor.fetchall()
        
        # Define columns for the report
        columns = [
            {"key": "title", "display_name": "Film Title", "format": "text"},
            {"key": "total_revenue", "display_name": "Total Revenue", "format": "currency"},
            {"key": "booking_count", "display_name": "Number of Bookings", "format": "integer"},
            {"key": "genre", "display_name": "Genre", "format": "text"},
            {"key": "age_rating", "display_name": "Age Rating", "format": "text"}
        ]
        
    return render_template(
        "generic_report.html", 
        report=report, 
        columns=columns,
        title="Top Revenue-Generating Films"
    )

@app.route('/report/staff_bookings')
@jwt_required()
def staff_bookings():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', b.booking_date) AS month,
                u.username AS staff_name,
                COUNT(b.id) AS booking_count,
                SUM(b.total_price) AS total_revenue
            FROM bookings b
            JOIN users u ON b.booking_staff_id = u.id
            GROUP BY month, u.username
            ORDER BY month DESC, booking_count DESC
        """)
        
        report = cursor.fetchall()
        
        # Define columns for the report
        columns = [
            {"key": "month", "display_name": "Month", "format": "text"},
            {"key": "staff_name", "display_name": "Staff Member", "format": "text"},
            {"key": "booking_count", "display_name": "Number of Bookings", "format": "integer"},
            {"key": "total_revenue", "display_name": "Total Revenue", "format": "currency"}
        ]
        
    return render_template(
        "generic_report.html", 
        report=report, 
        columns=columns,
        title="Monthly Staff Booking Performance"
    )
# ===============================
# 🔹 Predict Bookings
# ===============================
import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from flask import send_file

def get_db_connection():
    conn = sqlite3.connect("horizon_cinemas.db")
    conn.row_factory = sqlite3.Row
    return conn

def predict_future_bookings():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch historical booking data
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', booking_date) AS date, COUNT(*) AS total_bookings
            FROM bookings
            GROUP BY date
        """)
        df = pd.DataFrame(cursor.fetchall(), columns=["date", "total_bookings"])

        if df.empty:  # Check if there is no booking data
            return "No booking data available for predictions."

        df["date"] = pd.to_datetime(df["date"])
        df["days_since_start"] = (df["date"] - df["date"].min()).dt.days

        # Train Linear Regression Model
        X = df["days_since_start"].values.reshape(-1, 1)
        y = df["total_bookings"].values
        model = LinearRegression()
        model.fit(X, y)

        # Predict for the next 7 days
        future_days = np.array([df["days_since_start"].max() + i for i in range(1, 8)]).reshape(-1, 1)
        predictions = model.predict(future_days)

        # Plot Predictions
        plt.figure(figsize=(8, 4))
        plt.plot(df["date"], df["total_bookings"], label="Actual Bookings", marker="o")
        future_dates = pd.date_range(df["date"].max() + pd.Timedelta(days=1), periods=7)
        plt.plot(future_dates, predictions, label="Predicted Bookings", linestyle="dashed")
        plt.xlabel("Date")
        plt.ylabel("Bookings")
        plt.title("AI-Predicted Future Bookings")
        plt.legend()
        plt.savefig("static/charts/predicted_bookings.png")  # Save in static folder
        plt.close()

        return "Prediction completed and saved."

# ===============================
# 🔹 Route to Trigger AI Predictions
# ===============================
@app.route('/predict_bookings', methods=['GET'])
@jwt_required()
def get_predicted_bookings():
    """Generate AI-based future booking predictions and display the chart."""
    prediction_status = predict_future_bookings()
    return render_template("report.html", report=None, title="AI-Predicted Bookings", chart="static/charts/predicted_bookings.png")

# ===============================
# 🔹 Logout
# ===============================
@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = make_response(jsonify({"message": "✅ Logged out successfully!"}))
    unset_jwt_cookies(response)
    return response

# ===============================
# 🔹 Manager Login
# ===============================
from flask_jwt_extended import create_access_token, set_access_cookies

@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'GET':
        return render_template('manager_login.html')

    data = request.get_json() if request.is_json else request.form
    username = data.get("username")
    password = data.get("password")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(user[1], password):
        flash("Invalid username or password", "danger")
        return redirect(url_for('manager_login'))

    access_token = create_access_token(identity=str(user[0]))

    # ✅ Ensure JWT is set in cookies
    response = make_response(redirect(url_for('manager_dashboard')))
    set_access_cookies(response, access_token)  # 🔥 This line is critical!

    flash("✅ Manager Login successful!", "success")
    return response

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

    # ✅ Fetch booking summary with cinema names
    cursor.execute("""
        SELECT cinemas.city, COUNT(bookings.id) AS total_bookings, SUM(bookings.total_price) AS total_revenue
        FROM bookings
        JOIN showtimes ON bookings.showtime_id = showtimes.id
        JOIN cinemas ON showtimes.cinema_id = cinemas.id
        GROUP BY cinemas.city
    """)
    
    booking_summary = cursor.fetchall()  # ✅ Fetch data from DB

    return render_template(
        "manager_dashboard.html", 
        booking_summary=booking_summary, 
        manager_id=user_id
    )
# ===============================
# 🔹 Run Flask App
# ===============================
if __name__ == "__main__":
    app.run(debug=True, port=5003)