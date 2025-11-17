# app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return '@Filmyswap.in'


if __name__ == "__main__":
    app.run()
