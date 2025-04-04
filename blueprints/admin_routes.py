from flask import Blueprint, request, render_template, redirect, url_for, flash, make_response
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, set_access_cookies
from database.database_setup import get_db_connection
from datetime import datetime
import uuid
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

admin_routes = Blueprint('admin', __name__)

# ===============================
#  Admin Login
# ===============================
@admin_routes.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user["password"], password):
            if user["role"] not in ["admin", "manager"]:
                flash("❌ Unauthorized access!", "danger")
                return redirect(url_for('admin.admin_login'))

            access_token = create_access_token(identity=str(user["id"]))
            resp = make_response(redirect(url_for("admin.admin_dashboard")))
            set_access_cookies(resp, access_token)
            return resp

        flash("❌ Invalid username or password!", "danger")
    return render_template("admin_login.html")


# ===============================
#  Admin Dashboard
# ===============================
@admin_routes.route('/admin_dashboard')
@jwt_required(locations=["cookies"])
def admin_dashboard():
    user_id = get_jwt_identity()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch user role
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or user["role"] not in ["admin", "manager"]:
            flash("❌ Unauthorized access!", "danger")
            return redirect(url_for('admin.admin_login'))

        # Fetch films and related showtimes
        cursor.execute("""
            SELECT films.id AS film_id, films.title, films.genre, films.age_rating,
                   showtimes.cinema_id, GROUP_CONCAT(DISTINCT showtimes.show_time) AS showtimes
            FROM films
            LEFT JOIN showtimes ON films.id = showtimes.film_id
            GROUP BY films.id, showtimes.cinema_id
        """)
        film_rows = cursor.fetchall()

        films, film_cinemas = [], {}
        for row in film_rows:
            fid = row["film_id"]
            if not any(f["id"] == fid for f in films):
                films.append({
                    "id": fid,
                    "title": row["title"],
                    "genre": row["genre"],
                    "age_rating": row["age_rating"],
                    "showtimes": row["showtimes"] or "None"
                })
            if row["cinema_id"]:
                cursor.execute("SELECT id, city, location FROM cinemas WHERE id = ?", (row["cinema_id"],))
                cinema = cursor.fetchone()
                if cinema:
                    film_cinemas.setdefault(fid, []).append(cinema)

        # ✅ Build dropdown with all unique cinemas
        cinema_dropdown = []
        seen_ids = set()
        for clist in film_cinemas.values():
            for cinema in clist:
                if cinema["id"] not in seen_ids:
                    seen_ids.add(cinema["id"])
                    cinema_dropdown.append(cinema)

        # ✅ Optional fallback: If no showtime-based cinemas, grab all cinemas
        if not cinema_dropdown:
            cursor.execute("SELECT id, city, location FROM cinemas")
            cinema_dropdown = cursor.fetchall()

    return render_template("admin_dashboard.html",
                           admin_id=user_id,
                           films=films,
                           film_cinemas=film_cinemas,
                           cinema_dropdown=cinema_dropdown)


# ===============================
#  Add Redirect for /admin
# ===============================   
@admin_routes.route('/admin')
def admin_root():
    return redirect(url_for('admin.admin_dashboard'))

# ===============================
#  Add Film + Initial Showtimes
# ===============================
@admin_routes.route('/add_film', methods=['GET', 'POST'])
@jwt_required()
def add_film():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, city, location FROM cinemas")
        cinemas = cursor.fetchall()

        selected_cinema_id = request.args.get("cinema_id", type=int)
        selected_cinema_info = None
        screens = []

        if selected_cinema_id:
            cursor.execute("SELECT city, location FROM cinemas WHERE id = ?", (selected_cinema_id,))
            selected_cinema_info = cursor.fetchone()
            cursor.execute("SELECT screen_number FROM screens WHERE cinema_id = ?", (selected_cinema_id,))
            screens = [row["screen_number"] for row in cursor.fetchall()]

    if request.method == 'GET':
        return render_template("add_film.html",
                               cinemas=cinemas,
                               selected_cinema_id=selected_cinema_id,
                               selected_cinema_info=selected_cinema_info,
                               screens=screens)

    # POST logic
    title = request.form.get("title")
    genre = request.form.get("genre")
    age_rating = request.form.get("age_rating")
    description = request.form.get("description")
    showtimes = request.form.getlist("showtimes[]")
    screen_numbers = request.form.getlist("screens[]")

    # ✅ Validate cinema_id presence
    cinema_id_raw = request.form.get("cinema_id")
    if not cinema_id_raw:
        flash("❌ Cinema selection is required.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    cinema_id = int(cinema_id_raw)
    price = float(request.form.get("price"))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO films (title, genre, age_rating, description)
            VALUES (?, ?, ?, ?)
        """, (title, genre, age_rating, description))
        film_id = cursor.lastrowid

        for show_time, screen_number in zip(showtimes, screen_numbers):
            cursor.execute("""
                INSERT INTO showtimes (film_id, cinema_id, screen_number, show_time, price)
                VALUES (?, ?, ?, ?, ?)
            """, (film_id, cinema_id, int(screen_number), show_time, price))

        conn.commit()

    flash("✅ Film and showtimes added successfully!", "success")
    return redirect(url_for('admin.admin_dashboard'))
# ===============================
# Manage Films / Showtimes
# ===============================


@admin_routes.route('/manage_film', methods=['GET'])
@jwt_required()
def manage_film():
    user_id = get_jwt_identity()
    selected_cinema = request.args.get("cinema_id", type=int)
    selected_screen = request.args.get("screen_number", type=int)
    selected_date = request.args.get("date", datetime.now().strftime('%Y-%m-%d'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, city, location FROM cinemas")
        cinemas = cursor.fetchall()

        cursor.execute("SELECT * FROM films")
        films = cursor.fetchall()

        selected_cinema_info, screens, showtime_map = None, [], {}

        if selected_cinema:
            cursor.execute("SELECT city, location FROM cinemas WHERE id = ?", (selected_cinema,))
            selected_cinema_info = cursor.fetchone()
            cursor.execute("SELECT screen_number FROM screens WHERE cinema_id = ?", (selected_cinema,))
            screens = [row["screen_number"] for row in cursor.fetchall()]

            cursor.execute("""
                SELECT s.id AS showtime_id, s.screen_number, s.show_time, s.price,
                       f.title, f.id AS film_id
                FROM showtimes s
                JOIN films f ON f.id = s.film_id
                WHERE s.cinema_id = ? AND DATE(s.show_time) = ?
            """, (selected_cinema, selected_date))

            for row in cursor.fetchall():
                key = (row["screen_number"], row["show_time"][11:16])
                showtime_map[key] = {
                    "title": row["title"],
                    "showtime_id": row["showtime_id"],
                    "price": row["price"],
                    "film_id": row["film_id"]
                }

    return render_template("manage_film.html",
                           user_id=user_id,
                           cinemas=cinemas,
                           films=films,
                           screens=screens,
                           selected_cinema=selected_cinema,
                           selected_cinema_info=selected_cinema_info,
                           selected_date=selected_date,
                           selected_screen=selected_screen,
                           showtime_map=showtime_map,
                           cinema=selected_cinema_info,
                           cinema_id=selected_cinema)
# ===============================
#  Add Showtime Grid View
# ===============================
@admin_routes.route('/add_showtime/<int:cinema_id>', methods=['GET'])
@jwt_required()
def add_showtime(cinema_id):
    selected_date = request.args.get("date", datetime.now().strftime('%Y-%m-%d'))
    selected_film_id = request.args.get("film_id", type=int)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, city, location FROM cinemas WHERE id = ?", (cinema_id,))
        cinema = cursor.fetchone()
        if not cinema:
            flash("❌ Cinema not found.", "danger")
            return redirect(url_for('admin.manage_film', cinema_id=cinema_id))

        cursor.execute("SELECT id, title FROM films")
        films = cursor.fetchall()

        cursor.execute("SELECT screen_number FROM screens WHERE cinema_id = ?", (cinema_id,))
        screens = [row["screen_number"] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT s.screen_number, s.show_time, f.title
            FROM showtimes s
            JOIN films f ON s.film_id = f.id
            WHERE s.cinema_id = ? AND DATE(s.show_time) = ?
        """, (cinema_id, selected_date))

        showtime_map = {}
        for row in cursor.fetchall():
            time_slot = row["show_time"][11:16]  # "HH:MM"
            key = (row["screen_number"], time_slot)
            showtime_map[key] = row["title"]

        time_slots = [f"{hour:02}:00" for hour in range(10, 24)]

    return render_template("add_showtime.html",
                           cinema=cinema,
                           cinema_id=cinema_id,
                           films=films,
                           screens=screens,
                           selected_date=selected_date,
                           showtime_map=showtime_map,
                           time_slots=time_slots)

# ===============================
#  Add Showtime Ajax
# ===============================

@admin_routes.route('/add_showtime_ajax', methods=['POST'])
@jwt_required()
def add_showtime_ajax():
    data = request.form
    film_id = int(data.get("film_id"))
    cinema_id = int(data.get("cinema_id"))
    screen_number = int(data.get("screen_number"))
    time_slot = data.get("time_slot")
    date = data.get("date")

    show_time = f"{date} {time_slot}:00"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM films WHERE id = ?", (film_id,))
        film = cursor.fetchone()

        if not film:
            return {"success": False}, 400

        # You can customize pricing logic if needed
        price = 10.0

        cursor.execute("""
            INSERT INTO showtimes (film_id, cinema_id, screen_number, show_time, price)
            VALUES (?, ?, ?, ?, ?)
        """, (film_id, cinema_id, screen_number, show_time, price))
        conn.commit()

    return {"success": True, "title": film["title"]}


# ✅ This should be in admin_routes.py

@admin_routes.route('/delete_film/<int:film_id>', methods=['GET'])
@jwt_required()
def delete_film(film_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM films WHERE id = ?", (film_id,))
        cursor.execute("DELETE FROM showtimes WHERE film_id = ?", (film_id,))
        conn.commit()

    flash("✅ Film and related showtimes deleted.", "success")
    return redirect(url_for('admin.admin_dashboard'))

# ===============================
#  Select Cinema to Add Showtimes (when film has no cinema yet)
# ===============================
@admin_routes.route('/select_cinema_for_showtime/<int:film_id>', methods=['GET'])
@jwt_required()
def select_cinema_for_showtime(film_id):
    selected_date = request.args.get("date", datetime.now().strftime('%Y-%m-%d'))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, city, location FROM cinemas")
        cinemas = cursor.fetchall()

        cursor.execute("SELECT * FROM films WHERE id = ?", (film_id,))
        film = cursor.fetchone()

        if not film:
            flash("❌ Film not found.", "danger")
            return redirect(url_for('admin.admin_dashboard'))

        cursor.execute("SELECT screen_number FROM screens")
        screens = [row["screen_number"] for row in cursor.fetchall()]

        # Fixed hourly time slots
        time_slots = [f"{hour:02}:00" for hour in range(10, 24)]

        showtime_map = {}

        cursor.execute("""
            SELECT s.id, s.screen_number, s.show_time, f.title
            FROM showtimes s
            JOIN films f ON f.id = s.film_id
            WHERE DATE(s.show_time) = ?
        """, (selected_date,))
        for row in cursor.fetchall():
            key = (row["screen_number"], row["show_time"][11:16])
            showtime_map[key] = {
                "id": row["id"],
                "show_time": row["show_time"],
                "title": row["title"]
            }

    # Reuse select_cinema.html
    return render_template("select_cinema.html",
                           film=film,
                           cinema=cinemas[0] if cinemas else {},  # temporary for title
                           selected_date=selected_date,
                           screens=screens,
                           time_slots=time_slots,
                           showtime_map=showtime_map)

# ===============================
#  Update Film Info (from manage_film.html)
# ===============================
@admin_routes.route('/update_film/<int:film_id>', methods=['POST'])
@jwt_required()
def update_film(film_id):
    title = request.form.get("title")
    genre = request.form.get("genre")
    age_rating = request.form.get("age_rating")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE films
            SET title = ?, genre = ?, age_rating = ?
            WHERE id = ?
        """, (title, genre, age_rating, film_id))
        conn.commit()

    flash("✅ Film updated successfully!", "success")
    return redirect(url_for('admin.manage_film'))
