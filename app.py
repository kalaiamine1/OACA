import os
import datetime
from flask import Flask, send_from_directory, abort, redirect, request, jsonify

from configuration import ensure_default_user, get_meetings_collection
from login import auth_bp, _current_user_claims
from users import users_bp
from scores import scores_bp
from interview import interview_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path="",
)

# 🔹 Collection meetings
meetings_collection = get_meetings_collection()

# --- Blueprints ---
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(scores_bp)
app.register_blueprint(interview_bp)

# --- Routes principales ---
@app.route("/")
def root():
    claims = _current_user_claims()
    if not claims:
        return redirect("/login.html")
    if claims.get("role") == "admin":
        return redirect("/dashboard.html")
    return redirect("/home")

@app.route("/quiz.js")
def quiz_js():
    return send_from_directory(BASE_DIR, "quiz.js")

@app.route("/interview")
def interview_page():
    return send_from_directory(BASE_DIR, "interview.html")

@app.route("/home")
def home_page():
    return send_from_directory(BASE_DIR, "home.html")

@app.route("/login")
def login_page():
    return send_from_directory(BASE_DIR, "login.html")

@app.route("/signup")
def signup_page():
    return send_from_directory(BASE_DIR, "signup.html")

@app.route("/aviation_quiz_data.json")
def quiz_data():
    path = os.path.join(BASE_DIR, "aviation_quiz_data.json")
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(BASE_DIR, "aviation_quiz_data.json")

# --- Planifier une réunion ---
@app.route("/planify-interview", methods=["POST"])
def planify_interview():
    claims = _current_user_claims()
    if not claims or claims.get("role") != "admin":
        return jsonify(success=False, error="Accès refusé"), 403

    data = request.get_json()
    email = data.get("email")
    datetime_str = data.get("datetime")
    duration = data.get("duration")

    if not email or not datetime_str or not duration:
        return jsonify(success=False, error="Champs manquants")

    try:
        dt = datetime.datetime.fromisoformat(datetime_str)
    except Exception:
        return jsonify(success=False, error="Format de date invalide")

    if dt <= datetime.datetime.now():
        return jsonify(success=False, error="La date doit être dans le futur")

    zoom_link = "https://us05web.zoom.us/j/81160019257?pwd=Fu0o3yYFnBA1eRzTuCjwYk01Van3SW.1"

    meeting = {
        "email": email,
        "datetime": dt,
        "duration": int(duration),
        "zoom_link": zoom_link,
        "created_at": datetime.datetime.utcnow()
    }
    meetings_collection.insert_one(meeting)
    return jsonify(success=True, join_url=zoom_link)

# --- Récupérer toutes les réunions pour le dashboard admin ---
@app.route("/dashboard-meetings", methods=["GET"])
def dashboard_meetings():
    claims = _current_user_claims()
    if not claims or claims.get("role") != "admin":
        return jsonify(success=False, error="Accès refusé"), 403

    meetings_cursor = meetings_collection.find({}, {"_id": 0})
    meetings = []
    for m in meetings_cursor:
        meetings.append({
            "email": m["email"],
            "datetime": m["datetime"].isoformat(),
            "duration": m["duration"],
            "zoom_link": m["zoom_link"]
        })
    return jsonify(meetings)

# --- Serve any other top-level file directly ---
@app.route("/<path:filename>")
def serve_file(filename: str):
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(BASE_DIR, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ensure_default_user()
    app.run(host="0.0.0.0", port=port, debug=True)
