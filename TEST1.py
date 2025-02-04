import sqlite3
import tkinter as tk
from tkinter import messagebox

# Setup database function with a check for the role column
def setup_database():
    conn = sqlite3.connect('cinema_booking.db')
    cursor = conn.cursor()
    
    # Create the users table if it does not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # Check if the 'role' column exists in the 'users' table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'role' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
    
    # Create other tables
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cinemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            film_name TEXT,
            showtime TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Insert default admin and manager users
def insert_default_users():
    conn = sqlite3.connect('cinema_booking.db')
    cursor = conn.cursor()
    try:
        # Different usernames for admin and manager, but same password
        cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)", ("AdminFoyez", "123", "admin"))
        cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)", ("Foyez", "123", "manager"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Ignore if there is any integrity error
    finally:
        conn.close()

# Admin Login Page
class AdminLoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Login")
        
        tk.Label(self.root, text="Admin Username:").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)
        
        tk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)
        
        tk.Button(self.root, text="Login", command=self.verify_admin_login).pack(pady=20)

    def verify_admin_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect('cinema_booking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user and user[0] == "admin":
            messagebox.showinfo("Login Successful", "Welcome, Admin Dashboard!")
            self.root.destroy()
            AdminView().show_admin_view()
        else:
            messagebox.showerror("Login Failed", "Invalid Admin Username or Password")

# Manager Login Page
class ManagerLoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Manager Login")
        
        tk.Label(self.root, text="Manager Username:").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)
        
        tk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)
        
        tk.Button(self.root, text="Login", command=self.verify_manager_login).pack(pady=20)

    def verify_manager_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect('cinema_booking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user and user[0] == "manager":
            messagebox.showinfo("Login Successful", "Welcome, Manager Dashboard!")
            self.root.destroy()
            ManagerView().show_manager_view()
        else:
            messagebox.showerror("Login Failed", "Invalid Manager Username or Password")

# Admin View Class
class AdminView:
    def show_admin_view(self):
        self.admin_root = tk.Tk()
        self.admin_root.title("Admin Dashboard")

        tk.Label(self.admin_root, text="Admin Dashboard", font=("Arial", 16)).pack(pady=10)

        tk.Button(self.admin_root, text="Add Film", command=self.add_film).pack(pady=5)
        tk.Button(self.admin_root, text="Update Film", command=self.update_film).pack(pady=5)
        tk.Button(self.admin_root, text="Delete Film", command=self.delete_film).pack(pady=5)
        tk.Button(self.admin_root, text="Generate Reports", command=self.generate_reports).pack(pady=5)

        self.admin_root.geometry("500x400")
        self.admin_root.mainloop()

    def add_film(self):
        # Implementation for adding a film
        pass

    def update_film(self):
        # Placeholder for updating a film
        messagebox.showinfo("Info", "Update Film functionality not yet implemented.")

    def delete_film(self):
        # Placeholder for deleting a film
        messagebox.showinfo("Info", "Delete Film functionality not yet implemented.")

    def generate_reports(self):
        # Placeholder for generating reports
        messagebox.showinfo("Reports", "Reports functionality not yet implemented.")

# Manager View Class
class ManagerView:
    def show_manager_view(self):
        self.manager_root = tk.Tk()
        self.manager_root.title("Manager Dashboard")

        tk.Label(self.manager_root, text="Manager Dashboard", font=("Arial", 16)).pack(pady=10)

        tk.Button(self.manager_root, text="Add Cinema", command=self.add_cinema).pack(pady=5)
        tk.Button(self.manager_root, text="Manage Films", command=self.open_admin_view).pack(pady=5)
        self.manager_root.geometry("500x400")
        self.manager_root.mainloop()

    def add_cinema(self):
        add_cinema_window = tk.Toplevel(self.manager_root)
        add_cinema_window.title("Add Cinema")

        tk.Label(add_cinema_window, text="City:").pack(pady=5)
        city_entry = tk.Entry(add_cinema_window)
        city_entry.pack(pady=5)

        tk.Label(add_cinema_window, text="Cinema Name:").pack(pady=5)
        name_entry = tk.Entry(add_cinema_window)
        name_entry.pack(pady=5)

        def save_cinema():
            city = city_entry.get()
            name = name_entry.get()
            conn = sqlite3.connect('cinema_booking.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cinemas (city, name) VALUES (?, ?)", (city, name))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Cinema added successfully!")
            add_cinema_window.destroy()

        tk.Button(add_cinema_window, text="Save Cinema", command=save_cinema).pack(pady=10)

    def open_admin_view(self):
        AdminView().show_admin_view()

# Setup database and insert default users
setup_database()
insert_default_users()

# Main Login Selection Page
def main_login_selection():
    root = tk.Tk()
    root.title("Select Login Type")

    tk.Label(root, text="Select Login Type", font=("Arial", 14)).pack(pady=10)
    tk.Button(root, text="Admin Login", command=lambda: open_admin_login(root)).pack(pady=5)
    tk.Button(root, text="Manager Login", command=lambda: open_manager_login(root)).pack(pady=5)

    root.geometry("300x200")
    root.mainloop()

def open_admin_login(root):
    root.destroy()
    admin_root = tk.Tk()
    AdminLoginPage(admin_root)
    admin_root.geometry("300x250")
    admin_root.mainloop()

def open_manager_login(root):
    root.destroy()
    manager_root = tk.Tk()
    ManagerLoginPage(manager_root)
    manager_root.geometry("300x250")
    manager_root.mainloop()

# Start the main login selection page
main_login_selection()
