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

from configuration import get_db, USERS_COLLECTION, NOTIFICATIONS_COLLECTION, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_FROM_NAME
from login import _current_user_claims


users_bp = Blueprint("users", __name__)
TUNISIA_AIRPORTS = [
    "Tunis-Carthage (TUN)",
    "Enfidha–Hammamet (NBE)",
    "Monastir Habib Bourguiba (MIR)",
    "Sfax–Thyna (SFA)",
    "Djerba–Zarzis (DJE)",
    "Tozeur–Nefta (TOE)",
    "Gafsa–Ksar (GAF)",
    "Gabès–Matmata (GAE)",
    "Tabarka–Ain Draham (TBJ)",
    "Remada (RMA)",
]

@users_bp.route("/api/airports", methods=["GET"])  # list Tunisia airports
def list_airports():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(TUNISIA_AIRPORTS)


def generate_matricule():
    """Generate an 8-character matricule"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_password():
    """Generate a random 12-character password"""
    return ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=12))


def send_welcome_email(email, matricule, password, role):
    """Send welcome email with login credentials"""
    try:
        # Check if SMTP is configured
        if not SMTP_USERNAME or not SMTP_PASSWORD:
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
        
        NOTE: SMTP not configured. To send real emails, set these environment variables:
        - SMTP_USERNAME=your-email@gmail.com
        - SMTP_PASSWORD=your-app-password
        - SMTP_SERVER=smtp.gmail.com
        - SMTP_PORT=587
        - SMTP_FROM_EMAIL=noreply@oaca.local
        - SMTP_FROM_NAME=OACA Aviation System
        ========================================
        """)
            return True
        
        # Send actual email
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Welcome to OACA Aviation System"
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = email
        
        # Create HTML email content
        html_content = f"""
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
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Create server connection and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        server.sendmail(SMTP_FROM_EMAIL, email, msg.as_string())
        server.quit()
        
        print(f"Welcome email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_reset_email(email: str, temporary_password: str) -> bool:
    """Send password reset email with a new temporary password.
    If SMTP env is configured, try to send via SMTP; otherwise, log to console and return False
    so the caller can provide an in-app fallback.
    """
    try:
        smtp_server = os.environ.get("SMTP_SERVER", "")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_password = os.environ.get("SMTP_PASSWORD", "")
        sender_email = os.environ.get("SMTP_SENDER", smtp_user or "noreply@oaca.local")
        app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")

        if not smtp_server or not smtp_user or not smtp_password:
            # No SMTP configured
            print(f"""
            ========================================
            PASSWORD RESET FOR: {email}
            (SMTP not configured; showing in-console only)
            ========================================

            Temporary Password: {temporary_password}
            Login: {app_base_url}/login.html

            ========================================
            """)
            return False

        # Build email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "OACA – Password Reset"
        msg['From'] = sender_email
        msg['To'] = email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset=\"utf-8\" />
          <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
          <title>OACA – Password Reset</title>
        </head>
        <body style=\"margin:0; background:#0b1d44; color:#eaf2ff; font-family:Segoe UI,Roboto,Arial,sans-serif;\">
          <div style=\"max-width:640px; margin:0 auto; padding:24px;\">
            <div style=\"background:linear-gradient(135deg,#10265f,#0b1d44); border:1px solid rgba(255,255,255,0.15); border-radius:16px; overflow:hidden; box-shadow:0 12px 30px rgba(0,0,0,.35);\">
              <div style=\"padding:22px 22px 8px; text-align:center;\">
                <div style=\"width:56px;height:56px;margin:0 auto 10px; border-radius:14px; background:linear-gradient(135deg,#3b82f6,#60a5fa); display:flex; align-items:center; justify-content:center; font-weight:800; color:#fff;\">✈</div>
                <div style=\"font-size:22px; font-weight:800; letter-spacing:.2px;\">OACA Aviation</div>
                <div style=\"opacity:.8; font-size:13px;\">Aviation Administration System</div>
              </div>
              <div style=\"padding:16px 24px 6px;\">
                <h2 style=\"margin:10px 0 8px; font-size:20px;\">Password Reset</h2>
                <p style=\"margin:0 0 12px; line-height:1.55;\">We've generated a temporary password for your account. Use it to sign in, then update your password from your profile.</p>
                <div style=\"margin:18px 0; padding:14px 16px; border-radius:12px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18);\">
                  <div style=\"font-size:12px; opacity:.85; margin-bottom:6px;\">Temporary password</div>
                  <div style=\"font-family:Consolas,Menlo,monospace; font-weight:800; font-size:18px; color:#93c5fd;\">{temporary_password}</div>
                </div>
                <p style=\"margin:16px 0 22px;\">
                  <a href=\"{app_base_url}/login.html\" style=\"display:inline-block; padding:12px 18px; background:linear-gradient(135deg,#274bcc,#3b82f6); color:#ffffff; text-decoration:none; border-radius:10px; font-weight:700; box-shadow:0 8px 20px rgba(30,64,175,.35);\">Sign in to OACA</a>
                </p>
              </div>
              <div style=\"padding:16px 24px 22px; border-top:1px solid rgba(255,255,255,0.14); text-align:center; opacity:.8; font-size:12px;\">
                © OACA Aviation. This is an automated message.
              </div>
            </div>
          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send reset email: {e}")
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
    airport = str(body.get("airport", "")).strip()
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
        "airport": airport or None,
        "created_at": datetime.datetime.utcnow(),
    }
    
    users.insert_one(user_data)
    
    # Send welcome email
    email_sent = send_welcome_email(email, matricule, password, role)
    
    return jsonify({
        "ok": True, 
        "message": "User created successfully" + (" and welcome email sent" if email_sent else " but email failed to send"),
        "matricule": matricule,
        "email_sent": email_sent
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
    airport = body.get("airport")
    if isinstance(airport, str) and airport.strip():
        updates["airport"] = airport.strip()
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


@users_bp.route("/api/password/forgot", methods=["POST"])  # unauthenticated password reset request
def forgot_password():
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400
    db = get_db()
    users = db[USERS_COLLECTION]
    user = users.find_one({"email": email})
    # Respond 200 even if user not found (avoid enumeration)
    if not user:
        return jsonify({"ok": True})
    temp_password = generate_password()
    users.update_one({"email": email}, {"$set": {"password_hash": generate_password_hash(temp_password)}})
    sent_via_email = False
    try:
        sent_via_email = send_reset_email(email, temp_password)
    except Exception:
        sent_via_email = False
    # Best-effort notification entry
    try:
        db[NOTIFICATIONS_COLLECTION].insert_one({
            "email": email,
            "type": "password_reset",
            "title": "Password Reset",
            "message": "A temporary password was " + ("sent to your email." if sent_via_email else "generated. Email delivery failed; use the code shown in the reset dialog."),
            "created_at": datetime.datetime.utcnow(),
            "read": False,
        })
    except Exception:
        pass
    # If email couldn't be sent, return the temp password so the client can display it securely
    resp: Dict[str, Any] = {"ok": True, "via": "email" if sent_via_email else "fallback"}
    if not sent_via_email:
        resp["temporary_password"] = temp_password
    return jsonify(resp)


