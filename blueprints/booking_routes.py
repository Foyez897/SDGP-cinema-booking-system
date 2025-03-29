from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from database.database_setup import get_db_connection  
import traceback
from datetime import datetime
import logging
from flask_bcrypt import Bcrypt
from flask import current_app as app
from flask_jwt_extended import set_access_cookies
import uuid
from datetime import timedelta
import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from flask import send_file

bcrypt = Bcrypt()  # ✅ You must initialize it!
print("✅ booking_routes.py LOADED")

booking_routes = Blueprint('booking', __name__)


# ===============================
# 🔹 Booking Staff Login
# ===============================

@booking_routes.route('/staff_login', methods=['GET', 'POST'])
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
    
    response = make_response(redirect(url_for('booking.booking_page')))  # ✅ Redirect to booking page
    set_access_cookies(response, access_token)

    logging.info(f"DEBUG: JWT token set for {username}")
    return response  # ✅ Redirects to 'booking.html' instead of returning JSON

# ===============================
# 🔹 Booking Page 
# ===============================

@booking_routes.route('/booking')
@jwt_required()
def booking_page():
    """Renders the booking page with cinema selection."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ✅ Fetch list of cinemas for staff to choose from
        cursor.execute("SELECT id, city, location FROM cinemas")
        cinemas = cursor.fetchall()

    return render_template("booking.html", cinemas=cinemas, request=request)

# ===============================
# 🔹 Booking Home
# ===============================

@booking_routes.route('/', methods=['GET', 'POST'])
def home():
    print("📍 booking_routes: using get_db_connection()")  # 👈 add this

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, city, location FROM cinemas")
            cinemas = cursor.fetchall()

            selected_cinema_id = request.form.get("cinema_id")
            films = []

            if selected_cinema_id:
                cursor.execute("""
                    SELECT films.id, films.title, films.genre, films.age_rating, films.description,
                           GROUP_CONCAT(showtimes.show_time) AS showtimes
                    FROM films
                    JOIN showtimes ON films.id = showtimes.film_id
                    WHERE showtimes.cinema_id = ?
                    GROUP BY films.id
                """, (selected_cinema_id,))
                films = cursor.fetchall()

            return render_template("index.html", cinemas=cinemas, films=films)

    except Exception as e:
       import traceback
       print("❌ ERROR IN HOME ROUTE:\n", traceback.format_exc())
       return "Internal Server Error", 500


# ===============================
# 🔹 Select Cinema
# ===============================

@booking_routes.route('/select_cinema', methods=['GET'])
@jwt_required()
def select_cinema():
    cinema_id = request.args.get("cinema_id")
    selected_date = request.args.get("date")

    if not cinema_id:
        flash("❌ Please select a cinema first.", "danger")
        return redirect(url_for("booking.booking_page"))

    if not selected_date:
        selected_date = datetime.now().strftime('%Y-%m-%d')  # default to today

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get cinema info
        cursor.execute("SELECT city, location FROM cinemas WHERE id = ?", (cinema_id,))
        cinema = cursor.fetchone()
        if not cinema:
            flash("❌ Cinema not found!", "danger")
            return redirect(url_for("booking.booking_page"))

        # Get screens in this cinema
        cursor.execute("SELECT screen_number FROM screens WHERE cinema_id = ? ORDER BY screen_number", (cinema_id,))
        screens = [row["screen_number"] for row in cursor.fetchall()]

        # Define time slots
        time_slots = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]

        # Fetch showtimes only for the selected date
        cursor.execute("""
            SELECT showtimes.id AS id, show_time, screen_number, films.title
            FROM showtimes
            JOIN films ON showtimes.film_id = films.id
            WHERE cinema_id = ? AND DATE(show_time) = ?
        """, (cinema_id, selected_date))
        showtimes = cursor.fetchall()

        # Map showtimes into (screen, time) key
        showtime_map = {}
        for st in showtimes:
            time_str = st["show_time"][11:16]
            key = (st["screen_number"], time_str)
            showtime_map[key] = {
                "title": st["title"],
                "show_time": st["show_time"],
                "id": st["id"]
            }

    return render_template(
        "select_cinema.html",
        cinema=cinema,
        screens=screens,
        time_slots=time_slots,
        showtime_map=showtime_map,
        selected_date=selected_date
    )

# ===============================
# 🔹 Seat Availability 
# ===============================

@booking_routes.route('/view_showtime/<int:showtime_id>')
@jwt_required()
def view_showtime(showtime_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Step 1: Get showtime details
        cursor.execute("""
            SELECT showtimes.id, show_time, films.title, showtimes.screen_number, showtimes.cinema_id
            FROM showtimes
            JOIN films ON showtimes.film_id = films.id
            WHERE showtimes.id = ?
        """, (showtime_id,))
        showtime = cursor.fetchone()

        if not showtime:
            flash("❌ Showtime not found!", "danger")
            return redirect(url_for("booking.booking_page"))

        # Step 2: Get cinema city
        cursor.execute("SELECT city FROM cinemas WHERE id = ?", (showtime["cinema_id"],))
        city_result = cursor.fetchone()
        city = city_result["city"] if city_result else "Bristol"

        # Step 3: Get screen ID
        cursor.execute("""
            SELECT id FROM screens
            WHERE screen_number = ? AND cinema_id = ?
        """, (showtime["screen_number"], showtime["cinema_id"]))
        screen = cursor.fetchone()

        if not screen:
            flash("❌ Screen not found for this showtime!", "danger")
            return redirect(url_for("booking.booking_page"))

        screen_id = screen["id"]

        # Step 4: Fetch all seats with dynamic pricing
        cursor.execute("""
            SELECT s.id, s.seat_number, s.seat_type,
                   CASE WHEN b.id IS NOT NULL THEN 1 ELSE 0 END AS is_booked
            FROM seats s
            LEFT JOIN bookings b ON s.id = b.seat_id AND b.showtime_id = ?
            WHERE s.screen_id = ?
            ORDER BY s.seat_number
        """, (showtime_id, screen_id))
        seats = cursor.fetchall()

        seat_list = []
        for seat in seats:
            seat_dict = dict(seat)
            seat_dict["price"] = get_dynamic_price(
                city=city,
                show_time=showtime["show_time"],
                seat_type=seat_dict["seat_type"].replace("_", " ").title()
            )
            seat_list.append(seat_dict)

        # Step 5: Check discount eligibility
        from datetime import datetime

        showtime_dt = datetime.strptime(showtime["show_time"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        within_30_minutes = 0 <= (showtime_dt - now).total_seconds() <= 1800

        cursor.execute("SELECT COUNT(*) FROM seats WHERE screen_id = ?", (screen_id,))
        total_seats = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE showtime_id = ?", (showtime_id,))
        booked_seats = cursor.fetchone()[0]

        occupancy = booked_seats / total_seats if total_seats else 1
        below_70_percent = occupancy < 0.7

        discount_eligible = within_30_minutes and below_70_percent

    return render_template(
        "view_showtime.html",
        showtime=showtime,
        film={"title": showtime["title"]},
        seats=seat_list,
        discount_eligible=discount_eligible
    )

# ===============================
# 🔹 Dynamic Pricing Function
# ===============================

def get_dynamic_price(city, show_time, seat_type):
    # Parse time from show_time string
    show_time_obj = datetime.strptime(show_time, "%Y-%m-%d %H:%M:%S")
    hour = show_time_obj.hour

    # Define price grid
    base_prices = {
        "Birmingham": [5, 6, 7],
        "Bristol": [6, 7, 8],
        "Cardiff": [5, 6, 7],
        "London": [10, 11, 12]
    }

    # Determine time slot
    if 8 <= hour < 12:
        time_slot = 0  # Morning
    elif 12 <= hour < 17:
        time_slot = 1  # Afternoon
    else:
        time_slot = 2  # Evening

    base_price = base_prices.get(city, [6, 7, 8])[time_slot]

    if seat_type == "Upper Gallery":
        return round(base_price * 1.2, 2)
    elif seat_type == "VIP":
        return round((base_price * 1.2) * 1.2, 2)
    else:
        return round(base_price, 2)

# ===============================
# 🔹 Book Ticket API (Protected)
# ===============================

@booking_routes.route('/book', methods=['GET', 'POST'])
@jwt_required(optional=True, locations=["headers", "cookies"])
def book_tickets():
    if request.method == 'GET':
        # ✅ Redirect to main booking page instead of showing booking form
        return redirect(url_for('booking.home'))

    # ✅ POST: Booking logic remains the same
    try:
        user_id = get_jwt_identity()
        data = request.get_json() if request.is_json else request.form

        showtime_id = data.get("showtime_id")
        customer_name = data.get("customer_name")
        customer_email = data.get("customer_email")
        customer_phone = data.get("customer_phone")
        seat_ids = data.get("seat_ids")

        if not all([showtime_id, customer_name, customer_email, customer_phone, seat_ids]):
            return jsonify({"error": "Missing required fields"}), 400

        if isinstance(seat_ids, str):
            seat_ids = seat_ids.split(",")

        total_price = 0
        last_minute_discount_applied = False
        family_discount_applied = False
        booking_reference = str(uuid.uuid4())[:8]

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get showtime info
            cursor.execute("SELECT show_time, cinema_id FROM showtimes WHERE id = ?", (showtime_id,))
            showtime_data = cursor.fetchone()
            if not showtime_data:
                return jsonify({"error": "Invalid showtime ID"}), 400

            show_time, cinema_id = showtime_data
            show_dt = datetime.strptime(show_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()

            # Enforce 7-day booking limit
            if show_dt > now + timedelta(days=7):
                return jsonify({"error": "❌ You can only book tickets up to 7 days in advance."}), 400

            within_30_min = 0 <= (show_dt - now).total_seconds() <= 1800

            # Get city
            cursor.execute("SELECT city FROM cinemas WHERE id = ?", (cinema_id,))
            city_row = cursor.fetchone()
            city = city_row[0] if city_row else "Bristol"

            # Calculate occupancy
            cursor.execute("SELECT COUNT(*) FROM seats WHERE screen_id IN (SELECT id FROM screens WHERE cinema_id = ?)", (cinema_id,))
            total_seats = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM bookings WHERE showtime_id = ?", (showtime_id,))
            booked_seats = cursor.fetchone()[0]

            occupancy = booked_seats / total_seats if total_seats else 1
            apply_last_minute_discount = within_30_min and occupancy < 0.7
            apply_family_discount = len(seat_ids) >= 4

            for seat_id in seat_ids:
                cursor.execute("SELECT seat_type FROM seats WHERE id = ?", (seat_id,))
                seat_row = cursor.fetchone()
                if not seat_row:
                    return jsonify({"error": f"Seat ID {seat_id} not found"}), 400

                seat_type = seat_row[0]
                price = get_dynamic_price(city, show_time, seat_type)

                if apply_last_minute_discount:
                    price *= 0.75
                    last_minute_discount_applied = True

                if apply_family_discount:
                    price *= 0.80
                    family_discount_applied = True

                total_price += price

                cursor.execute("""
                    INSERT INTO bookings (
                        customer_name, customer_email, customer_phone,
                        showtime_id, seat_id, booking_reference,
                        total_price, booking_staff_id, booking_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    customer_name, customer_email, customer_phone,
                    showtime_id, seat_id, booking_reference,
                    price, user_id, now.strftime("%Y-%m-%d %H:%M:%S")
                ))

                cursor.execute("UPDATE seats SET is_booked = 1 WHERE id = ?", (seat_id,))

            conn.commit()

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            staff_name = user_row["username"] if user_row else "Unknown"

        message = "✅ Booking successful!"
        if last_minute_discount_applied:
            message += " 🎉 25% last-minute discount applied!"
        if family_discount_applied:
            message += " 👨‍👩‍👧‍👦 20% family discount applied!"

        return jsonify({
            "message": message,
            "booking_reference": booking_reference,
            "total_price": round(total_price, 2),
            "staff_name": staff_name
        }), 201

    except Exception as e:
        import traceback
        print("❌ BOOKING ERROR:", traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500
# ===============================
# 🔹 AI Model: Predict Future Booking Demand
# ===============================

@booking_routes.route('/report/bookings_per_film')
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


@booking_routes.route('/report/monthly_revenue')
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


@booking_routes.route('/report/top_film')
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


@booking_routes.route('/report/staff_bookings')
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

def get_db_connection():
    conn = sqlite3.connect("database/horizon_cinemas.db")
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
# 🔹 Pedict Bookings
# ===============================   

@booking_routes.route('/predict_bookings', methods=['GET'])
def predict_bookings():
    time_slots = np.array([10, 14, 18, 21]).reshape(-1, 1)
    bookings = np.array([50, 80, 120, 100])

    model = LinearRegression()
    model.fit(time_slots, bookings)

    predicted_bookings = model.predict(np.array([[20]]))
    return jsonify({"predicted_bookings_for_8PM": int(predicted_bookings[0])})

# ===============================
# 🔹 Route to Trigger AI Predictions
# ===============================

@booking_routes.route('/predict_bookings', methods=['GET'])
@jwt_required()
def get_predicted_bookings():
    """Generate AI-based future booking predictions and display the chart."""
    prediction_status = predict_future_bookings()
    return render_template("report.html", report=None, title="AI-Predicted Bookings", chart="static/charts/predicted_bookings.png")

# ===============================
# 🔹 Logout
# ===============================

@booking_routes.route('/refund', methods=['GET', 'POST'])
@jwt_required()
def refund_page():
    booking = None
    search_query = request.args.get('ref')  # booking reference or email

    if search_query:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id AS booking_id, b.booking_reference, b.customer_name, b.customer_email,
                       b.customer_phone, b.total_price, b.booking_date,
                       f.title AS film_title, s.show_time, seats.seat_number
                FROM bookings b
                JOIN showtimes s ON b.showtime_id = s.id
                JOIN films f ON s.film_id = f.id
                JOIN seats ON b.seat_id = seats.id
                WHERE b.booking_reference = ? OR b.customer_email = ?
            """, (search_query, search_query))
            rows = cursor.fetchall()

            if rows:
                seat_numbers = [row["seat_number"] for row in rows]
                total_price = sum(row["total_price"] for row in rows)

                booking = dict(rows[0])
                booking["seat_numbers"] = seat_numbers
                booking["total_price"] = round(total_price, 2)
                booking["booking_id"] = rows[0]["booking_id"]

    return render_template("refund.html", booking=booking, request=request)

# ===============================
# 🔹 Process Refund
# ===============================

@booking_routes.route('/process_refund', methods=['POST'])
@jwt_required()
def process_refund():
    booking_id = request.form.get("booking_id")

    if not booking_id:
        flash("❌ Booking ID is missing!", "danger")
        return redirect(url_for('booking.refund_page'))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get booking reference from any one booking
        cursor.execute("""
            SELECT booking_reference FROM bookings WHERE id = ?
        """, (booking_id,))
        ref_row = cursor.fetchone()

        if not ref_row:
            flash("❌ Booking not found!", "danger")
            return redirect(url_for('booking.refund_page'))

        booking_reference = ref_row["booking_reference"]

        # Fetch all bookings with this reference
        cursor.execute("""
            SELECT b.id, b.total_price, s.show_time, b.seat_id
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.id
            WHERE b.booking_reference = ?
        """, (booking_reference,))
        bookings = cursor.fetchall()

        if not bookings:
            flash("❌ No bookings found for refund!", "danger")
            return redirect(url_for('booking.refund_page'))

        showtime_str = bookings[0]["show_time"]
        from datetime import datetime, timedelta
        showtime_dt = datetime.strptime(showtime_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        if showtime_dt - now < timedelta(days=1):
            flash("❌ Refunds can only be processed at least 1 day in advance.", "danger")
            return redirect(url_for('booking.refund_page', ref=booking_reference))

        original_total = sum(b["total_price"] for b in bookings)
        refund_amount = round(original_total * 0.5, 2)

        for b in bookings:
            cursor.execute("DELETE FROM bookings WHERE id = ?", (b["id"],))
            cursor.execute("UPDATE seats SET is_booked = 0 WHERE id = ?", (b["seat_id"],))

        conn.commit()

    flash(f"✅ Refund processed! £{refund_amount} will be returned to the customer.", "success")
    return redirect(url_for('booking.refund_page', ref=booking_reference))

# ===============================
# 🔹 Receipt
# ===============================

@booking_routes.route('/receipt/<booking_ref>')
@jwt_required()
def receipt(booking_ref):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all booking rows with the same reference
        cursor.execute("""
            SELECT b.booking_reference, b.booking_date, b.customer_name,
                   b.customer_email, b.customer_phone, b.total_price,
                   f.title AS film_title, s.show_time, s.screen_number,
                   c.city, c.location, u.username AS staff_name, seats.seat_number
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.id
            JOIN films f ON s.film_id = f.id
            JOIN cinemas c ON s.cinema_id = c.id
            JOIN users u ON b.booking_staff_id = u.id
            JOIN seats ON b.seat_id = seats.id
            WHERE b.booking_reference = ?
        """, (booking_ref,))
        rows = cursor.fetchall()

        if not rows:
            return "Booking not found", 404

        # Group info
        seat_numbers = [r["seat_number"] for r in rows]
        total_price = sum(r["total_price"] for r in rows)

        # Take shared info from first row
        details = dict(rows[0])
        details["seat_numbers"] = seat_numbers
        details["total_price"] = round(total_price, 2)

    return render_template("receipt.html", booking=details)


# ===============================
# 🔹 Run Flask App
# ===============================
if __name__ == "__main__":
    app.run(debug=True, port=5000)