from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this for better security
bcrypt = Bcrypt(app)

# Database Setup
def setup_database():
    conn = sqlite3.connect('cinema_booking.db')
    cursor = conn.cursor()

    # Create users table with role column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Create films table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            genre TEXT,
            description TEXT,
            actors TEXT,
            age_rating TEXT,
            showtimes TEXT
        )
    ''')

    # Create cinemas table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cinemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            name TEXT
        )
    ''')

    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            film_name TEXT,
            showtime TEXT
        )
    ''')

    # Insert default admin and manager users
    hashed_password = bcrypt.generate_password_hash("123").decode('utf-8')
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("Foyez", hashed_password, "admin"))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("ManagerFoyez", hashed_password, "manager"))

    conn.commit()
    conn.close()

# Call database setup
setup_database()

# Home (Login Selection)
@app.route('/')
def home():
    return render_template('index.html')

# Admin Login Route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('cinema_booking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ? AND role = 'admin'", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[0], password):
            session['username'] = username
            session['role'] = 'admin'
            flash('Admin Login Successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Credentials!', 'danger')

    return render_template('admin_login.html')

# Manager Login Route
@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('cinema_booking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ? AND role = 'manager'", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[0], password):
            session['username'] = username
            session['role'] = 'manager'
            flash('Manager Login Successful!', 'success')
            return redirect(url_for('manager_dashboard'))
        else:
            flash('Invalid Credentials!', 'danger')

    return render_template('manager_login.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Unauthorized Access!', 'danger')
        return redirect(url_for('home'))

    return render_template('admin_dashboard.html', username=session['username'])

# Manager Dashboard
@app.route('/manager_dashboard')
def manager_dashboard():
    if 'username' not in session or session.get('role') != 'manager':
        flash('Unauthorized Access!', 'danger')
        return redirect(url_for('home'))

    return render_template('manager_dashboard.html', username=session['username'])

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)