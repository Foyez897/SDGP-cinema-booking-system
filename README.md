# 🎬 Cinema Booking System

A collaborative **Cinema Booking System** built with **Flask** and **SQLite**. This system allows **admins and managers** to manage cinemas, films, and bookings efficiently.

## 🚀 Features
✅ **User Authentication** (Admin & Manager Login)  
✅ **Manage Films** (Add, Update, Delete)  
✅ **Manage Cinemas** (Add Cinema Locations)  
✅ **Booking System** (Users can book movie tickets)  
✅ **SQLite Database** for storing information  
✅ **Flask Web Framework** for handling backend logic  
✅ **Secure Password Storage** with `bcrypt`  
✅ **Bootstrap-based UI** for a clean interface  

---

## 📂 **Project Structure**

cinema-booking-system/
│── app.py                 # Main Flask application
│── database_setup.py       # Script to setup database
│── requirements.txt        # Project dependencies
│── .gitignore              # Ignored files (e.g., virtual environment)
│── README.md               # Project documentation
│
├── static/                 # Static files (CSS, JavaScript, Images)
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── images/             # Images
│
└── templates/              # HTML templates for Flask
├── index.html          # Homepage / Login selection
├── admin_login.html    # Admin Login Page
├── manager_login.html  # Manager Login Page
├── admin_dashboard.html # Admin Dashboard
├── manager_dashboard.html # Manager Dashboard

---

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

Now, open http://127.0.0.1:5000/ in your browser.

🎭 User Roles & Login Credentials
Role	Username	    Password
Admin	Foyez	        123
Manager	ManagerFoyez	123


🏗 How to Contribute
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