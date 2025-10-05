from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash

from configuration import (
    get_db,
    USERS_COLLECTION,
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    JWT_EXPIRES_MIN,
)
from jwthelper import create_jwt, verify_jwt


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    if not request.is_json:
        return jsonify({"error": "Expected JSON body"}), 400
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    
    # Check if it's matricule login or email/password login
    if "matricule" in body:
        # Matricule login
        matricule = str(body.get("matricule", "")).strip().upper()
        if not matricule or len(matricule) != 8:
            return jsonify({"error": "Valid 8-character matricule is required"}), 400
        
        user = get_db()[USERS_COLLECTION].find_one({"matricule": matricule})
        if not user:
            return jsonify({"error": "Invalid matricule"}), 401
        
        email = user.get("email", "")
        role = user.get("role", "user")
    else:
        # Email/password login
        email = str(body.get("email", "")).strip().lower()
        password = str(body.get("password", ""))
        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        user = get_db()[USERS_COLLECTION].find_one({"email": email})
        if not user or not check_password_hash(user.get("password_hash", ""), password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        role = user.get("role", "user")

    token = create_jwt({"sub": str(user.get("_id")), "email": email, "role": role})
    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        max_age=JWT_EXPIRES_MIN * 60,  # 15 minutes by default
    )
    return resp


@auth_bp.route("/api/logout", methods=["POST"]) 
def api_logout():
    resp = make_response(jsonify({"ok": True}))
    # Invalidate cookie immediately
    resp.set_cookie(COOKIE_NAME, "", expires=0, path="/", httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
    return resp


def _current_user_claims() -> Optional[Dict[str, Any]]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_jwt(token)


@auth_bp.route("/api/me", methods=["GET"]) 
def api_me():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "email": claims.get("email"),
        "role": claims.get("role"),
        "name": claims.get("name"),
    })


