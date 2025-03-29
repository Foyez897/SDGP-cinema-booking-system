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
├── run.py                    # Flask entry point
├── requirements.txt
├── Procfile                  # For deployment (e.g., Heroku/Gunicorn)
├── extensions.py             # Global extensions (Bcrypt, JWT manager)
├── app/
│   └── __init__.py           # Flask app factory
├── blueprints/
│   ├── admin_routes.py       # Admin functionality
│   ├── booking_routes.py     # Booking operations
│   └── manager_routes.py     # Manager reports
├── database/
│   ├── database_setup.py     # SQLite schema setup
│   ├── horizon_cinemas.db    # Main SQLite database
│   ├── all_data.txt          # Sample exported data
│   └── export_all_data.py    # Export script
├── static/
│   ├── charts/               # Report chart images
│   ├── style.css             # Custom styling
├── templates/
│   ├── admin_dashboard.html
│   ├── manage_film.html
│   ├── booking.html
│   ├── select_cinema.html
│   ├── ...


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


🎭 User Roles & Login Credentials
Role	Username	    Password
Staff   staff1          Staff!Pass789
Admin	admin1	        Admin123Pass_
Manager	manager1	    anager@Pass456


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