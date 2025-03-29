from app import create_app

app = create_app()  # <-- add parentheses to actually call the function

if __name__ == "__main__":
    app.run(debug=True)