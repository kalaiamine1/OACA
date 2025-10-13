import os
import datetime
from flask import Flask, send_from_directory, abort, redirect, request, jsonify

from configuration import ensure_default_user
from login import auth_bp, _current_user_claims
from users import users_bp
from scores import scores_bp
from questions import questions_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path="",
)


# --- Blueprints ---
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(scores_bp)
app.register_blueprint(questions_bp)

# --- Routes principales ---
@app.route("/")
def root():
    # Default landing goes to public home; login pages handle auth flows
    return redirect("/home")

@app.route("/quiz.js")
def quiz_js():
    return send_from_directory(BASE_DIR, "quiz.js")


@app.route("/home")
def home_page():
    return send_from_directory(BASE_DIR, "home.html")

@app.route("/login")
def login_page():
    return send_from_directory(BASE_DIR, "login.html")

@app.route("/signup")
def signup_page():
    return send_from_directory(BASE_DIR, "signup.html")

@app.route("/assigned_quiz.html")
def assigned_quiz_page():
    return send_from_directory(BASE_DIR, "assigned_quiz.html")

@app.route("/quiz_setup.html")
def quiz_setup_page():
    return send_from_directory(BASE_DIR, "quiz_setup.html")

@app.route("/quiz_guide.html")
def quiz_guide_page():
    return send_from_directory(BASE_DIR, "quiz_guide.html")

@app.route("/aviation_quiz_data.json")
def quiz_data():
    path = os.path.join(BASE_DIR, "aviation_quiz_data.json")
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(BASE_DIR, "aviation_quiz_data.json")


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
