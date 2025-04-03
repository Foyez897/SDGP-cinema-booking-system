# 🎬 Horizon Cinemas Booking System (HCBS)

A robust, modular cinema booking system built using **Flask**, with secure role-based access, dynamic showtime management, and reporting dashboards. Designed for Admins, Managers, and Booking Staff.


## 🚀 Key Features

🔑 Role-Based Access Control (RBAC)
System behavior and views are based on user roles (Admin, Manager, Staff).
🔌 RESTful API Endpoints
APIs available for ticket booking, report generation, and seat availability queries.
🧩 Modular Codebase with Blueprints
Scalable and clean architecture using Flask Blueprints.
🛡️ Secure Password Hashing
User passwords are hashed using bcrypt before storage.
🎬 Cinema & Film Management
Admins can add, update, delete films and assign showtimes to multiple cinemas and screens.
🎟️ Ticket Booking System
Staff can book tickets for customers with real-time seat availability checks.
📅 Date Restrictions
Booking allowed only within a 7-day window from the current date.
🤖 AI-Powered Booking Predictions
Integrated scikit-learn models to forecast showtime demand using historical data.
📊 Graphical Insights
Matplotlib-based charts provide visual reports for revenue, bookings per film, staff activity, etc.
🧾 Reports & Admin Tools
Includes top-performing films, monthly revenue per cinema, and staff performance reports.


## 📁 Project Structure

.
├── Procfile                              # 🔁 For deployment (e.g., Heroku) – defines the entry point
├── README.md                             # 📘 Project overview and instructions
├── app
│   └── __init__.py                       # ⚙️ App factory: configures Flask, extensions, and blueprints
├── blueprints                            # 📦 Modular route logic split by user roles
│   ├── admin_routes.py                   # 👩‍💼 Admin dashboard, login, and film management
│   ├── booking_routes.py                 # 🎟️ Booking functionality and staff login
│   └── manager_routes.py                 # 🧑‍💼 Manager dashboard, cinema/screen management
├── clean_report.html                     # 📊 Optional cleaned-up report output (possibly for download or print)
├── database
│   ├── all_data.txt                      # 📄 Raw exported data (optional – for backup or testing)
│   ├── database_setup.py                 # 🛠️ Handles database connections (incl. test mode)
│   ├── export_all_data.py                # 📤 Script to dump/export data
│   ├── horizon_cinemas.db                # 🧠 Main production SQLite database
│   └── horizon_cinemas_test.db           # 🧪 Separate DB for testing (isolated from production)
├── instance                              # ⚠️ Can be deleted if truly unused – used in some Flask configs (e.g., per-env settings)
├── report.html                           # 📈 Possibly legacy or sample report output
├── requirements.txt                      # 📦 All Python dependencies for the project
├── run.py                                # 🚀 Main entry point (runs the Flask app)
├── static                                # 🎨 Static files (CSS, JS, images)
│   ├── images                            # 🖼️ Icons or image assets (optional)
│   ├── js                                # 📜 JavaScript files (if any)
│   └── style.css                         # 🎨 Main CSS styling file (used by all templates)
├── templates                             # 🧩 Jinja2 HTML templates (all UI pages)
│   ├── add_cinema.html                   # ➕ Add new cinema + screens
│   ├── add_film.html                     # ➕ Add new film
│   ├── add_showtime.html                 # ➕ Add showtime for a film
│   ├── admin_dashboard.html              # 🧠 Admin homepage/dashboard
│   ├── admin_login.html                  # 🔐 Admin login form
│   ├── admin_manage_cinemas.html         # 🛠️ Admin cinema management
│   ├── booking.html                      # 🎫 Booking interface for staff
│   ├── cinema_timetable.html             # 🕒 View timetable (per cinema)
│   ├── edit_screens.html                 # ✏️ Edit screens for a cinema
│   ├── generic_report.html               # 📋 Template for displaying flexible report tables
│   ├── index.html                        # 🏠 Homepage showing today’s films
│   ├── manage_cinemas.html               # 🗂️ Manager-access cinema control
│   ├── manage_film.html                  # 🎬 Manage films and showtimes
│   ├── manager_dashboard.html            # 📊 Manager overview dashboard
│   ├── manager_login.html                # 🔐 Manager login form
│   ├── monthly_revenue_report.html       # 💰 Monthly revenue breakdown
│   ├── receipt.html                      # 🧾 Booking confirmation receipt
│   ├── refund.html                       # 💸 Refund form
│   ├── report.html                       # 📈 Possibly legacy report (specific or outdated)
│   ├── select_cinema.html                # 🎥 Cinema selector before booking/showtime mgmt
│   ├── staff_login.html                  # 🔐 Staff login form
│   └── view_showtime.html                # 🕒 View individual showtime and seat layout
└── tests                                 # ✅ All Pytest-based unit & integration tests
    ├── __init__.py                       # 📦 Marks the tests folder as a Python package
    ├── conftest.py                       # 🧪 Global test fixtures (e.g., test client & DB setup)
    ├── test_admin_cinema_screen.py       # 🧪 Tests cinema/screen admin creation
    ├── test_admin_curd_film.py           # 🧪 Tests film add/edit/delete
    ├── test_auth_access_control.py       # 🔒 Verifies login access control per role
    ├── test_booking_block_expired.py     # 🧪 Tests that expired showtimes can't be booked
    ├── test_helpers.py                   # 🧰 Seed helpers for tests (DB setup utils)
    └── test_valid_booking.py             # ✅ Tests a full successful booking

8 directories, 48 files

## 🛠 **Setup & Installation**

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/Foyez897/cinema-booking-system.git
cd cinema-booking-system

2️⃣ Create a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows


## 🚀 Running the Application

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask server**
   ```bash
   python run.py
   ```
Now, open http://127.0.0.1:5000

## 🔐 Role-Based Access Control (RBAC)

The system follows strict role-based access as per assessment requirements:

- 👤 **Manager** can access:
  - Manager Dashboard (add/edit cinemas, screens)
  - Admin Dashboard (view reports, manage films)
  - Booking Dashboard

- 👤 **Admin** can access:
  - Admin Dashboard
  - Booking Dashboard
  - ❌ Cannot access Manager Dashboard (cannot manage cinemas or screens)

- 👤 **Booking Staff** can access:
  - Booking Dashboard only

This logic is enforced in the backend by checking the user’s role before allowing access to protected views.

🎭 User Roles & Login Credentials
Role	  Username	    Password
Staff   staff1        Staff!Pass789
Admin	  admin1	      Admin123Pass_
Manager	manager1	    Manager@Pass456


## 🔐 Security Features

- **JWT Authentication (via Secure Cookies):**
  - Tokens created using `flask-jwt-extended`
  - Stored in HTTP-only cookies for enhanced security
  - Role-checked access to admin, manager, and staff views

- **Password Hashing:**
  - All user passwords are hashed with **Flask-Bcrypt**
  - Plain passwords are never stored

## 🧱 Blueprint-Based Modular Design

The project uses Flask **Blueprints** to separate business logic:

| Module           | Responsibility                          |
|------------------|------------------------------------------|
| `admin_routes.py` | Film/showtime management, reports       |
| `booking_routes.py` | Ticket booking, cancellations          |
| `manager_routes.py` | Analytics, dashboards, monthly insights |


## 🎟️ API: Booking Endpoint

The system also supports **programmatic access** to the booking flow:

### 🔸 `POST /book`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

**Request JSON:**
```json
{
  "film_id": 3,
  "cinema_id": 1,
  "screen_number": 2,
  "showtime": "2025-04-01 19:00",
  "seats": ["A1", "A2"],
  "booking_user_id": 5
}


**Response:**
```json
{
  "status": "success",
  "message": "Booking confirmed.",
  "booking_reference": "BK235711"
}


> 🔐 Requires valid login and JWT token


## 📊 Admin/Manager Features

- ✅ Add/Edit/Delete films and showtimes
- 📅 View cinema timetables
- 📉 Real-time reports:
  - Bookings per film
  - Monthly revenue by cinema
  - Top-performing films
  - Staff booking activity
- 🧠 AI-based booking suggestions (where applicable)

🧪 Running Tests

The system includes thorough unit, integration, and system tests using pytest, covering core functionalities.

✅ Covered Test Areas

	•	Authentication & Role Enforcement
	•	Ensures login restrictions (e.g., Admin can’t access Manager view, but Manager can access Admin)
	•	Booking Logic
	•	Validates dynamic pricing, date restrictions, cancellation policies
	•	Database Seeding & Isolation
	•	Uses a separate test DB (horizon_cinemas_test.db) to avoid affecting production data
	•	Cinema, Film, Showtime, Seat Operations
	•	Create/edit/delete flows are tested across roles

🔧 How to Run Tests Locally

Make sure your virtual environment is activated and run:
   pytest --cov=app tests/

📁 A clean_report.html coverage report is also included for visual review.

📈 Future Enhancements
	•	AI-Based Demand Forecasting
    Planned integration of ML models to analyze past booking trends and predict future high-demand shows for:
	•	Smart pricing adjustments
	•	Auto-recommendation of showtimes
	•	Optimized staff allocation


## 🏗 How to Contribute
We welcome contributions! Follow these steps:
	1.	Fork the repository on GitHub.
	2.	Clone your forked repo:git clone https://github.com/your-username/cinema-booking-system.git
  3.	Create a new feature branch:git checkout -b feature-new-functionality
  4.	Make your changes & commit:git add .
      git commit -m "Added new feature"
  5.	Push to your fork & submit a pull request:git push origin feature-new-functionality

🚀 Git Workflow for the Team
  1.	Before working on a new feature, update your local repo:git pull origin main
  2.	Create a feature branch:git checkout -b feature-name
  3.	After making changes, commit & push:git add .
      git commit -m "Implemented feature-name"
      git push origin feature-name
  4.	Submit a pull request (PR) on GitHub and request a code review.

📜 License
This project is open-source and available under the MIT License.


© 2025 Horizon Cinemas — All Rights Reserved.