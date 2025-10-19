import os
import datetime
import logging
import random
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, g, make_response
from flask_cors import CORS
from flask_session import Session
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_CODE = os.getenv("SECRET_BUDDY_CODE")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or not SECRET_CODE:
    raise RuntimeError("Missing SECRET_KEY or SECRET_BUDDY_CODE from .env file")


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config.update(
    {
        "SESSION_COOKIE_SECURE": True,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Strict",
    }
)

Session(app)

CORS(app, origins=["https://potion-chats.onrender.com"], supports_credentials=True)

logging.basicConfig(level=logging.INFO)

MESSAGES = {}


def token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("jwt")

        auth_header = request.headers.get("Authorization", "")
        if not token and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Missing auth token"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.current_user = payload["user"]
            return function(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token is expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return wrapper


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get-token", methods=["POST"])
def gen_token():
    code = request.json.get("username")
    display_name = request.json.get("displayName")

    if code != SECRET_CODE or not display_name:
        return jsonify({"error": "Wrong code or missing chat name 😞"}), 401

    payload = {
        "user": display_name,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    logging.info(f"Issued token for {display_name}")

    session["displayName"] = display_name

    response = make_response(jsonify({"success": True}), 200)
    response.set_cookie(
        "jwt", token, httponly=True, secure=True, samesite="Strict", max_age=60 * 60
    )
    return response


@app.route("/secure-endpoint", methods=["GET"])
@token_required
def secure_endpoint():
    auth_header = request.headers.get("Authorization", "")
    logging.info(f"Auth header from {request.remote_addr}: {auth_header}")

    if auth_header.startswith("Bearer "):
        token = auth_header.split()[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return jsonify(
                {
                    "user": g.current_user,
                    "status": "active",
                    "message": "Welcome to the cool kid's club!",
                }
            ), 200
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Your token is expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return jsonify({"error": "Missing or broken auth header"}), 401


@app.route("/room/<int:room_id>/guess", methods=["POST"])
@token_required
def check_guess(room_id):
    guess = request.json.get("guess", 0)
    key = f"room_{room_id}_secret"
    secret = session.get(key)

    if not secret:
        return jsonify({"error": "Session expired. Reload the room."}), 400

    if guess < secret:
        result = "Too low 🥲"
    elif guess > secret:
        result = "Too high 🥲"
    else:
        result = "Correct! Welcome in friend 👋"
        session[f"room_{room_id}_access"] = True

    return jsonify({"result": result})


@app.route("/room/<int:room_id>")
@token_required
def room(room_id):
    key = f"room_{room_id}_secret"
    if key not in session:
        session[key] = random.randint(1, 5)

    themes = {
        1: "theme-vaporwave",
        2: "theme-arcade",
        3: "theme-neon-noir",
        4: "theme-cyber-green",
        5: "theme-crimson-fuzz",
    }
    theme_class = themes.get(room_id, "theme-default")

    return render_template("room.html", room_id=room_id, theme_class=theme_class)


@app.route("/rooms")
@token_required
def rooms():
    return render_template("rooms.html", rooms=range(1, 6))


@app.route("/room/<int:room_id>/chat", methods=["POST"])
@token_required
def chat(room_id):
    access_key = f"room_{room_id}_access"

    if not session.get(access_key):
        return jsonify({"error": "Acess denied"}), 403

    data = request.get_json() or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "Empty message"}), 400

    entry = {
        "user": g.current_user,
        "message": msg,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    MESSAGES.setdefault(room_id, []).append(entry)

    return jsonify({"message": msg}), 200


@app.route("/room/<int:room_id>/messages", methods=["GET"])
@token_required
def get_messages(room_id):
    if not room_id:
        return jsonify({"error": "ROOM ID WAS NOT FOUND IN GET_MESSAGES"})

    return jsonify(MESSAGES.get(room_id, [])), 200


def main():
    app.run(debug=True)


def create_app():
    load_dotenv()
    secret_code = os.getenv("SECRET_BUDDY_CODE")
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or not secret_code:
        raise RuntimeError("Missing SECRET_KEY or SECRET_BUDDY_CODE")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    @app.route("/")
    def home():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    main()
