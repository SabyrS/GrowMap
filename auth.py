import re
import logging
from flask import request, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from db import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('growmap_auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_password(password):
    """
    Validate password according to security requirements:
    - Minimum 12 characters
    - Must contain at least one letter (A-Z, a-z)
    - Must contain at least one digit (0-9)
    - Must contain at least one special character (!@#$%^&*)
    - Must not contain SQL injection dangerous characters
    
    Returns: (is_valid, error_message)
    """
    errors = []
    
    # Check minimum length
    if len(password) < 12:
        errors.append("Пароль должен содержать минимум 12 символов")
        logger.warning(f"Password validation failed: Too short (length={len(password)})")
    
    # Check for letters
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', password):
        errors.append("Пароль должен содержать буквы")
        logger.warning("Password validation failed: No letters found")
    
    # Check for digits
    if not re.search(r'\d', password):
        errors.append("Пароль должен содержать цифры")
        logger.warning("Password validation failed: No digits found")
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*\-_=+\[\]{}()|;:\'",.<>?/\\`~]', password):
        errors.append("Пароль должен содержать спецсимволы (!@#$%^&* и др.)")
        logger.warning("Password validation failed: No special characters found")
    
    # Check for SQL injection attempts - forbid dangerous patterns
    dangerous_patterns = [
        r"('\s*(or|and)|--|\*|;|xp_|sp_|\bselect\b|\bunion\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b)",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, password, re.IGNORECASE):
            errors.append("Пароль содержит недопустимые символы или последовательности")
            logger.warning(f"Password validation failed: Dangerous pattern detected - {pattern}")
            break
    
    if errors:
        return False, " | ".join(errors)
    
    logger.info("Password validation successful")
    return True, ""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        logger.info(f"Login attempt for user: {username}")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            logger.info(f"Login successful for user: {username}")
            return redirect("/")
        else:
            logger.warning(f"Login failed for user: {username} (invalid credentials)")
            return render_template("login.html", error="Неверный логин или пароль")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        logger.info(f"Registration attempt for user: {username}")

        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            logger.warning(f"Registration failed for {username}: {error_msg}")
            return render_template("register.html", error=error_msg)

        # Validate username (basic checks)
        if len(username) < 3:
            logger.warning(f"Registration failed for {username}: Username too short")
            return render_template("register.html", error="Имя пользователя должно содержать минимум 3 символа")
        
        if len(username) > 50:
            logger.warning(f"Registration failed: Username too long")
            return render_template("register.html", error="Имя пользователя слишком длинное")
        
        # Check for invalid characters in username (basic SQL injection prevention)
        if not re.match(r'^[a-zA-Z0-9_\-а-яА-ЯёЁ]+$', username):
            logger.warning(f"Registration failed for {username}: Invalid characters in username")
            return render_template("register.html", error="Имя пользователя содержит недопустимые символы")

        password_hash = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            logger.info(f"Registration successful for user: {username}")
        except Exception as e:
            conn.close()
            logger.error(f"Registration error for {username}: {str(e)}")
            return render_template(
                "register.html",
                error="Пользователь уже существует"
            )

        conn.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
