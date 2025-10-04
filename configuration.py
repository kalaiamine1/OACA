import os
import datetime
from typing import Optional

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# --- Charger les variables d'environnement (.env) ---
load_dotenv()

# --- Paramètres App et sécurité ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "OACA")

USERS_COLLECTION = "users"
SCORES_COLLECTION = "scores"
MEETINGS_COLLECTION = "meetings"  # 🔹 Ajout de la collection meetings
NOTIFICATIONS_COLLECTION = "notifications"
ASSIGNMENTS_COLLECTION = "quiz_assignments"

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "15"))

COOKIE_NAME = "access_token"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")

# --- Connexion MongoDB ---
_mongo_client: Optional[MongoClient] = None

def get_db():
    """
    Retourne l'objet base de données MongoDB.
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI)
    return _mongo_client[DB_NAME]

def get_meetings_collection():
    """
    Retourne la collection meetings.
    """
    db = get_db()
    return db[MEETINGS_COLLECTION]

def ensure_default_user() -> None:
    """
    Crée l'utilisateur admin par défaut s'il n'existe pas.
    """
    db = get_db()
    users = db[USERS_COLLECTION]
    default_email = os.environ.get("DEFAULT_USER_EMAIL", "admin@oaca.local").lower()
    default_password = os.environ.get("DEFAULT_USER_PASSWORD", "ChangeMe123!")
    if users.find_one({"email": default_email}):
        return
    users.insert_one({
        "email": default_email,
        "password_hash": generate_password_hash(default_password),
        "role": "admin",
        "created_at": datetime.datetime.utcnow(),
    })
