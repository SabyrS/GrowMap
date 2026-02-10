from flask import Flask
from db import init_db
import os
import secrets

app = Flask(__name__)

# Generate secure secret key
if "SECRET_KEY" in os.environ:
    app.secret_key = os.environ["SECRET_KEY"]
else:
    # For development only - in production use environment variable
    app.secret_key = secrets.token_hex(32)

# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send over HTTPS (set False for local development)
    SESSION_COOKIE_HTTPONLY=True,  # No access from JavaScript
    SESSION_COOKIE_SAMESITE="Lax",  # CSRF protection
    PERMANENT_SESSION_LIFETIME=86400  # 24 hours
)

init_db()

from auth import *
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
