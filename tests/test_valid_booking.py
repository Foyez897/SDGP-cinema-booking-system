from tests.test_helpers import seed_test_db

def test_valid_booking(client):
    showtime_id, seat_id = seed_test_db()

    response = client.post('/book', json={
        "showtime_id": showtime_id,
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_phone": "1234567890",
        "seat_ids": [str(seat_id)]
    })

    assert response.status_code == 200
    assert b"Booking Confirmed" in response.data or b"success" in response.data.lower()