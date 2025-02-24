import requests

# 🔹 Copy your actual JWT token from browser's cookies
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczOTQwOTQwNywianRpIjoiNWRjODZhYjQtYTQ1Ny00OGU1LThmNmQtZjViYjRlMjAwMDA4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3Mzk0MDk0MDcsImNzcmYiOiI3MWQ0MTlhMS1lMzlmLTRhOGItYmNmZi1jMGQ5N2UzYjg2NWUiLCJleHAiOjE3Mzk0OTU4MDd9.4WNkc46T402ehtkGaksxd5tY30hplihrYF660a5MQ2I"

# 🔹 Correct Flask endpoint
url = "http://127.0.0.1:5003/admin_dashboard"

# 🔹 Send request with JWT token in the cookies
cookies = {"access_token_cookie": jwt_token}  # Ensure this name matches Flask-JWT-Extended

response = requests.get(url, cookies=cookies)

# 🔹 Print the response
print("Status Code:", response.status_code)
print("Response JSON:", response.json())