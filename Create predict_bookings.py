import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt

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
        df["date"] = pd.to_datetime(df["date"])
        df["days_since_start"] = (df["date"] - df["date"].min()).dt.days

        # Train Linear Regression Model
        X = df["days_since_start"].values.reshape(-1, 1)
        y = df["total_bookings"].values
        model = LinearRegression()
        model.fit(X, y)

        # Predict for next 7 days
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
        plt.savefig("static/charts/predicted_bookings.png")
        plt.close()

if __name__ == "__main__":
    predict_future_bookings()
    