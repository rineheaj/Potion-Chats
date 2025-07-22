import os
import datetime
import logging
import random

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Missing SECRET_KEY from .env file")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get-token", methods=["POST"])
def gen_token():
    data = request.get_json() or {}
    username = data.get("username")

    if username == "friend":
        payload = {
            "user": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        logging.info(f"Issued token for {username}")
        return jsonify({"token": token})
    
    return jsonify({"error": "Sorry, that is not the secret code 😞"}), 401


@app.route("/secure-endpoint", methods=["GET"])
def secure_endpoint():
    auth_header = request.headers.get("Authorization", "")
    logging.info(f"Auth header from {request.remote_addr}: {auth_header}")

    if auth_header.startswith("Bearer "):
        token = auth_header.split()[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return jsonify({"message": "Welcome to the cool kid's club!"}), 200
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "You're token is expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
    
    return jsonify({"error": "Missing or broken auth header"}), 401


@app.route("/room/<int:room_id>/guess", methods=["POST"])
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
def room(room_id):
    key = f"room_{room_id}_secret"
    if key not in session:
        session[key] = random.randint(1,5)
    return render_template("room.html", room_id=room_id)

@app.route("/room/<int:room_id>/chat", methods=["POST"])
def chat(room_id):
    access_key = f"room_{room_id}_access"
    
    if not session.get(access_key):
        return jsonify({"error": "Acess denied"}), 403
    
    data = request.get_json() or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "Empty message"}), 400
    
    return jsonify({"message": msg}), 200



def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
