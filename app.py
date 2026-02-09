from flask import Flask
from db import init_db

app = Flask(__name__)
app.secret_key = "secret"

init_db()

from auth import *
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
