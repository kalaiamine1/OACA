import datetime
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict
import os

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from configuration import get_db, USERS_COLLECTION, NOTIFICATIONS_COLLECTION
from login import _current_user_claims


users_bp = Blueprint("users", __name__)


def generate_matricule():
    """Generate an 8-character matricule"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_password():
    """Generate a random 12-character password"""
    return ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=12))


def send_welcome_email(email, matricule, password, role):
    """Send welcome email with login credentials"""
    try:
        # For now, we'll just log the credentials and return True
        # In production, you would configure actual SMTP settings
        print(f"""
        ========================================
        WELCOME EMAIL FOR: {email}
        ========================================
        
        Your OACA Aviation System account has been created!
        
        Login Credentials:
        - Email: {email}
        - Matricule: {matricule}
        - Password: {password}
        - Role: {role.upper()}
        
        Login Options:
        1. Use email + password
        2. Use matricule only
        
        Access the system at: http://localhost:8000/login.html
        
        ========================================
        """)
        
        # In production, uncomment and configure the SMTP settings below:
        """
        smtp_server = "smtp.gmail.com"  # Your SMTP server
        smtp_port = 587
        sender_email = "noreply@oaca.local"  # Your sender email
        sender_password = "your_app_password"  # Your app password
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Welcome to OACA Aviation System"
        msg['From'] = sender_email
        msg['To'] = email
        
        # Create HTML email content (same as before)
        html_content = f\"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to OACA</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background: linear-gradient(135deg, #0b1d44 0%, #0a1a3d 100%);
                    border-radius: 16px;
                    padding: 40px;
                    box-shadow: 0 12px 30px rgba(0,0,0,0.25);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #3b82f6, #60a5fa);
                    border-radius: 50%;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    color: white;
                    font-weight: bold;
                }}
                h1 {{
                    color: #e6eeff;
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .subtitle {{
                    color: #9db0d9;
                    margin: 8px 0 0;
                    font-size: 16px;
                }}
                .content {{
                    background: rgba(255,255,255,0.08);
                    border-radius: 12px;
                    padding: 30px;
                    margin: 20px 0;
                    border: 1px solid rgba(255,255,255,0.14);
                }}
                .credentials {{
                    background: rgba(59, 130, 246, 0.1);
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .credential-item {{
                    margin: 10px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .credential-label {{
                    font-weight: 600;
                    color: #e6eeff;
                }}
                .credential-value {{
                    font-family: 'Courier New', monospace;
                    background: rgba(0,0,0,0.2);
                    padding: 8px 12px;
                    border-radius: 4px;
                    color: #60a5fa;
                    font-weight: bold;
                }}
                .login-info {{
                    background: rgba(34, 197, 94, 0.1);
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .login-info h3 {{
                    color: #22c55e;
                    margin: 0 0 10px;
                }}
                .login-info p {{
                    color: #e6eeff;
                    margin: 5px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #9db0d9;
                    font-size: 14px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #3b82f6, #60a5fa);
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                }}
                .warning {{
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .warning p {{
                    color: #ef4444;
                    margin: 0;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">OACA</div>
                    <h1>Welcome to OACA Aviation</h1>
                    <p class="subtitle">Aviation Administration System</p>
                </div>
                
                <div class="content">
                    <p style="color: #e6eeff; font-size: 16px; margin: 0 0 20px;">
                        Your account has been successfully created! You can now access the OACA Aviation System using the credentials below.
                    </p>
                    
                    <div class="credentials">
                        <h3 style="color: #e6eeff; margin: 0 0 15px; text-align: center;">Your Login Credentials</h3>
                        <div class="credential-item">
                            <span class="credential-label">Email:</span>
                            <span class="credential-value">{email}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Matricule:</span>
                            <span class="credential-value">{matricule}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Password:</span>
                            <span class="credential-value">{password}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Role:</span>
                            <span class="credential-value">{role.upper()}</span>
                        </div>
                    </div>
                    
                    <div class="login-info">
                        <h3>How to Login</h3>
                        <p><strong>Option 1:</strong> Use your email and password</p>
                        <p><strong>Option 2:</strong> Use your matricule (8-character code)</p>
                        <p>Both methods will give you access to the same account.</p>
                    </div>
                    
                    <div class="warning">
                        <p>⚠️ Please save these credentials securely. You can change your password after logging in.</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:8000/login.html" class="button">Access OACA System</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2024 OACA Aviation Company. All rights reserved.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        \"\"\"
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        """
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@users_bp.route("/api/users", methods=["POST"])  # admin creates user
def create_user():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    role = str(body.get("role", "user"))
    if not email:
        return jsonify({"error": "email is required"}), 400
    
    users = get_db()[USERS_COLLECTION]
    if users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 409
    
    # Generate matricule and password
    matricule = generate_matricule()
    password = generate_password()
    
    # Ensure matricule is unique
    while users.find_one({"matricule": matricule}):
        matricule = generate_matricule()
    
    # Create user
    user_data = {
        "email": email,
        "matricule": matricule,
        "password_hash": generate_password_hash(password),
        "role": role,
        "created_at": datetime.datetime.utcnow(),
    }
    
    users.insert_one(user_data)
    
    # Send welcome email
    email_sent = send_welcome_email(email, matricule, password, role)
    
    return jsonify({
        "ok": True, 
        "message": "User created successfully" + (" and welcome email sent" if email_sent else " but email failed to send"),
        "matricule": matricule
    })


@users_bp.route("/api/users", methods=["GET"])  # admin list users
def list_users():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    cursor = get_db()[USERS_COLLECTION].find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1)
    return jsonify(list(cursor))


@users_bp.route("/api/profile", methods=["GET"])  # current user profile
def get_profile():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    user = db[USERS_COLLECTION].find_one({"email": claims.get("email")}, {"_id": 0, "password_hash": 0})
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify(user)


@users_bp.route("/api/profile", methods=["PUT"])  # update profile fields (no password here)
def update_profile():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    updates: Dict[str, Any] = {}
    name = body.get("name")
    if isinstance(name, str) and name.strip():
        updates["name"] = name.strip()
    username = body.get("username")
    if isinstance(username, str) and username.strip():
        updates["username"] = username.strip()
    cin = body.get("cin")
    if isinstance(cin, str) and cin.isdigit() and len(cin) == 8:
        updates["cin"] = cin
    # Optional avatar URL (set by upload endpoint)
    avatar_url = body.get("avatar_url")
    if isinstance(avatar_url, str) and avatar_url.strip():
        updates["avatar_url"] = avatar_url.strip()
    if not updates:
        return jsonify({"error": "No updates"}), 400
    db = get_db()
    db[USERS_COLLECTION].update_one({"email": claims.get("email")}, {"$set": updates})
    return jsonify({"ok": True})


@users_bp.route("/api/profile/reset_password", methods=["POST"])  # change password via old/new (repurposed)
def reset_password():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    if not isinstance(old_password, str) or not isinstance(new_password, str) or not new_password:
        return jsonify({"error": "old_password and new_password are required"}), 400
    db = get_db()
    user = db[USERS_COLLECTION].find_one({"email": claims.get("email")})
    if not user or not check_password_hash(user.get("password_hash", ""), old_password):
        return jsonify({"error": "Old password is incorrect"}), 400
    db[USERS_COLLECTION].update_one({"email": claims.get("email")}, {"$set": {"password_hash": generate_password_hash(new_password)}})
    return jsonify({"ok": True})


# Removed separate change_password endpoint to consolidate on reset_password


@users_bp.route("/api/profile/avatar", methods=["POST"])  # upload avatar file and set URL
def upload_avatar():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    # Prefix filename with user identifier to avoid collisions
    user_prefix = claims.get("email", "user")
    safe_prefix = "".join(c for c in user_prefix if c.isalnum())
    final_name = f"{safe_prefix}_{filename}"
    file_path = os.path.join(upload_dir, final_name)
    file.save(file_path)
    # Public URL relative to app static root
    public_url = f"/uploads/avatars/{final_name}"
    db = get_db()
    db[USERS_COLLECTION].update_one({"email": claims.get("email")}, {"$set": {"avatar_url": public_url}})
    return jsonify({"ok": True, "avatar_url": public_url})


@users_bp.route("/api/notifications", methods=["GET"])  # list current user's notifications
def list_notifications():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    cursor = db[NOTIFICATIONS_COLLECTION].find({"email": claims.get("email")}, {"_id": 0}).sort("created_at", -1)
    return jsonify(list(cursor))


@users_bp.route("/api/notifications/read", methods=["POST"])  # mark notifications as read
def mark_notifications_read():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    db[NOTIFICATIONS_COLLECTION].update_many({"email": claims.get("email"), "read": False}, {"$set": {"read": True}})
    return jsonify({"ok": True})


