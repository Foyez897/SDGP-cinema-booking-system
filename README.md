# 🎬 Horizon Cinemas Booking System

A Flask-powered Cinema Booking System with JWT Authentication, SQLite Database, and Gunicorn Deployment. This system allows Admins, Managers, and Booking Staff to manage cinemas, films, and bookings securely and efficiently.

## 🚀 Key Features

✅ JWT Authentication with flask_jwt_extended (Admin, Manager, Booking Staff)
✅ Secure Password Hashing with bcrypt
✅ Role-Based Access Control (RBAC)
✅ Cinema & Film Management (Add, Update, Delete)
✅ Ticket Booking System (Staff Can Book for Customers)
✅ Real-Time Seat Availability Check
✅ Booking Restrictions (No bookings beyond 7 days)
✅ AI-Powered Booking Predictions using sklearn
✅ Admin & Manager Dashboards
✅ Graphical Booking Insights (Matplotlib charts)
✅ RESTful API Support for Booking and Reports
✅ Production-Ready Deployment with Gunicorn 

---

## 📂 **Project Structure**

horizon-cinemas/
│── app.py                 # Main Flask application
│── database_setup.py       # Database setup script
│── requirements.txt        # Project dependencies
│── .gitignore              # Ignore virtual env, cache files, etc.
│── Procfile                # Deployment instructions for Heroku/Gunicorn
│── README.md               # Project documentation
│
├── static/                 # Static assets (CSS, JS, Charts)
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── images/             # UI Images
│   ├── charts/             # Generated Reports (PNG)
│
├── templates/              # Flask HTML templates
│   ├── index.html          # Homepage
│   ├── admin_login.html    # Admin Login Page
│   ├── manager_login.html  # Manager Login Page
│   ├── staff_login.html    # Booking Staff Login
│   ├── admin_dashboard.html # Admin Dashboard
│   ├── manager_dashboard.html # Manager Dashboard
│   ├── booking.html        # Booking Interface
│   ├── report.html         # Reports & AI Predictions
│   ├── add_film.html       # Add New Films
│   ├── update_film.html    # Update Existing Films
│
└── instance/               # SQLite database storage

## 🛠 **Setup & Installation**

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/Foyez897/cinema-booking-system.git
cd cinema-booking-system

2️⃣ Create a Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Setup the Database
python database_setup.py

5️⃣ Run the Application
python app.py

Now, open http://127.0.0.1:5003/ & http://localhost. in your browser.

🎭 User Roles & Login Credentials
Role	Username	    Password
Staff   staff1          Staff!Pass789
Admin	admin1	        Admin123Pass_
Manager	manager1	    anager@Pass456

### 🚀 Deploying to Production
### ••1️⃣ Run Gunicorn Locally••
'''sh
gunicorn app:app --bind 0.0.0.0:5003 --workers 4

## 🛠 API Endpoints

🔹 Authentication

 • POST /staff_login → Logs in Booking Staff
 • POST /admin_login → Logs in Admin
 • POST /manager_login → Logs in Manager

🔹 Booking & Management

 • POST /book → Book a ticket (Requires JWT)
 • GET /booking → Booking page (Requires JWT)
 • GET /admin_dashboard → Admin panel (Requires JWT)
 • GET /manager_dashboard → Manager panel (Requires JWT)

🔹 Reports & Predictions

 • GET /report/bookings_per_film → View Bookings per Film
 • GET /predict_bookings → AI Predictions for Future Bookings



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

    
✨ Future Improvements
🚀 User Registration & Authentication System
🚀 Online Payment Integration for Bookings
🚀 Movie Rating & Reviews
🚀 Automated Testing with GitHub Actions