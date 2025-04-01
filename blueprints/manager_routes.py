from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from database.database_setup import get_db_connection  
import traceback
from flask_bcrypt import Bcrypt
from flask_jwt_extended import unset_jwt_cookies
from flask_jwt_extended import create_access_token, set_access_cookies
bcrypt = Bcrypt()  # ✅ You must initialize it!

manager_routes = Blueprint('manager', __name__)


# ===============================
#  Manager Login
# ===============================

@manager_routes.route('/manager_login', methods=['GET', 'POST'])
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
        return redirect(url_for('manager.manager_login'))

    access_token = create_access_token(identity=str(user[0]))

    # ✅ Ensure JWT is set in cookies
    response = make_response(redirect(url_for('manager.manager_dashboard')))
    set_access_cookies(response, access_token)  # 🔥 This line is critical!

    flash("✅ Manager Login successful!", "success")
    return response

# ===============================
#  Managera Dashboard
# ===============================

@manager_routes.route('/manager_dashboard', methods=['GET'])
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
    SELECT films.id, films.title, films.genre, films.age_rating,
           GROUP_CONCAT(DISTINCT showtimes.show_time) AS showtimes
    FROM films
    LEFT JOIN showtimes ON films.id = showtimes.film_id AND showtimes.show_time > CURRENT_TIMESTAMP
    GROUP BY films.id
""")

    
    booking_summary = cursor.fetchall()  # ✅ Fetch data from DB

    return render_template(
        "manager_dashboard.html", 
        booking_summary=booking_summary, 
        manager_id=user_id
    )

# ===============================
#  Manager logout
# ===============================

@manager_routes.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = make_response(jsonify({"message": "✅ Logged out successfully!"}))
    unset_jwt_cookies(response)
    return response

# ===============================
#  Add New Cinema
# ===============================

@manager_routes.route('/add_cinema', methods=['GET', 'POST'])
@jwt_required(locations=["cookies"])
def add_cinema():
    user_id = get_jwt_identity()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user["role"] not in ["manager", "admin"]:
            flash("❌ Unauthorized access!", "danger")
            return redirect(url_for("home"))

    if request.method == 'GET':
        return render_template("add_cinema.html")

    # Handle POST
    city = request.form.get("city")
    address = request.form.get("address")
    num_of_screens = int(request.form.get("num_of_screens", 1))
    seat_config = request.form.get("seat_config", "all")

    if not city or not address:
        flash("❌ All fields are required!", "danger")
        return redirect(url_for("manager.add_cinema"))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Step 1: Insert Cinema
        cursor.execute(
            "INSERT INTO cinemas (city, location, num_of_screens) VALUES (?, ?, ?)",
            (city, address, num_of_screens)
        )
        cinema_id = cursor.lastrowid

        # Step 2: Add Screens + Generate Seats
        for i in range(1, num_of_screens + 1):
            screen_number = i

            if seat_config == "all":
                total_seats = int(request.form.get("total_seats_all", 50))
                vip_count = int(request.form.get("vip_count_all", 0))  # ← ✅ read from form
            else:
                total_seats = int(request.form.get(f"total_seats_{i}", 50))
                vip_count = int(request.form.get(f"vip_count_{i}", 0))  # ← ✅ read from form

            cursor.execute(
                "INSERT INTO screens (cinema_id, screen_number, total_seats) VALUES (?, ?, ?)",
                (cinema_id, screen_number, total_seats)
            )
            screen_id = cursor.lastrowid

            generate_seats(cursor, screen_id, total_seats, vip_count)

        conn.commit()

    flash("✅ New cinema and screens added successfully!", "success")
    return redirect(url_for("manager.manager_dashboard"))

# ===============================
#  Manage Cinemas
# ===============================

@manager_routes.route('/manage_cinemas', methods=['GET'])
@jwt_required()
def manage_cinemas():
    user_id = get_jwt_identity()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user["role"] not in ["admin", "manager"]:
            flash("❌ Unauthorized access!", "danger")
            return redirect(url_for("home"))

        # ✅ Updated query to dynamically count screens
        cursor.execute("""
            SELECT c.id, c.city, c.location, COUNT(s.id) AS num_of_screens
            FROM cinemas c
            LEFT JOIN screens s ON c.id = s.cinema_id
            GROUP BY c.id
        """)
        cinemas = cursor.fetchall()

    return render_template("manage_cinemas.html", cinemas=cinemas)

# ===============================
#  Edit Screens
# ===============================

@manager_routes.route('/edit_screens/<int:cinema_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_screens(cinema_id):
    user_id = get_jwt_identity()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user["role"] not in ["manager", "admin"]:
            flash("❌ Unauthorized", "danger")
            return redirect(url_for("home"))

        if request.method == "POST":
            action = request.form.get("action")
            screen_id = request.form.get("screen_id")
            total_seats = int(request.form.get("total_seats", 0))

            if action == "add":
                screen_number = request.form.get("screen_number")

                # Insert screen
                cursor.execute(
                    "INSERT INTO screens (cinema_id, screen_number, total_seats) VALUES (?, ?, ?)",
                    (cinema_id, screen_number, total_seats)
                )
                screen_id = cursor.lastrowid

                # Generate seats
                generate_seats(cursor, screen_id, total_seats)
                conn.commit()
                flash("✅ Screen added successfully!", "success")

            elif action == "update":
                # Delete existing seats and regenerate
                cursor.execute("DELETE FROM seats WHERE screen_id = ?", (screen_id,))
                cursor.execute(
                    "UPDATE screens SET total_seats = ? WHERE id = ?",
                    (total_seats, screen_id)
                )
                generate_seats(cursor, screen_id, total_seats)
                conn.commit()
                flash("✅ Screen updated!", "success")

            elif action == "remove":
                cursor.execute("DELETE FROM seats WHERE screen_id = ?", (screen_id,))
                cursor.execute("DELETE FROM screens WHERE id = ?", (screen_id,))
                conn.commit()
                flash("🗑️ Screen removed", "info")

        # Refresh screen list after POST
        cursor.execute(
            "SELECT id, screen_number, total_seats FROM screens WHERE cinema_id = ? ORDER BY screen_number",
            (cinema_id,)
        )
        screens = cursor.fetchall()

        cursor.execute("SELECT city, location FROM cinemas WHERE id = ?", (cinema_id,))
        cinema = cursor.fetchone()

    return render_template("edit_screens.html", screens=screens, cinema=cinema, cinema_id=cinema_id)

# 🔽 Helper Function
def generate_seats(cursor, screen_id, total_seats, vip_count=10):
    lower = round(total_seats * 0.3)
    vip = min(vip_count, total_seats - lower)  # Ensure VIPs don't exceed available
    upper = total_seats - lower - vip
    seat_number = 1

    for _ in range(lower):
        cursor.execute("INSERT INTO seats (screen_id, seat_number, seat_type, is_booked) VALUES (?, ?, ?, 0)",
                       (screen_id, seat_number, "Lower Hall"))
        seat_number += 1

    for _ in range(upper):
        cursor.execute("INSERT INTO seats (screen_id, seat_number, seat_type, is_booked) VALUES (?, ?, ?, 0)",
                       (screen_id, seat_number, "Upper Gallery"))
        seat_number += 1

    for _ in range(vip):
        cursor.execute("INSERT INTO seats (screen_id, seat_number, seat_type, is_booked) VALUES (?, ?, ?, 0)",
                       (screen_id, seat_number, "VIP"))
        seat_number += 1

# ===============================
#  Delete Cinema
# ===============================

@manager_routes.route('/delete_cinema/<int:cinema_id>', methods=['POST'])
@jwt_required()
def delete_cinema(cinema_id):
    user_id = get_jwt_identity()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user["role"] not in ["admin", "manager"]:
            flash("❌ Unauthorized access!", "danger")
            return redirect(url_for("home"))

        cursor.execute("DELETE FROM cinemas WHERE id = ?", (cinema_id,))
        conn.commit()

    flash("🗑️ Cinema deleted successfully!", "success")
    return redirect(url_for("manager.manage_cinemas"))
