import datetime
from typing import Any, Dict, List
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, jsonify, request

from configuration import get_db, SCORES_COLLECTION, USERS_COLLECTION, ASSIGNMENTS_COLLECTION, NOTIFICATIONS_COLLECTION, USER_ATTEMPTS_COLLECTION
from login import _current_user_claims


scores_bp = Blueprint("scores", __name__)
def _send_success_email(target_email: str, correct: int, total: int, percentage: float, per_section: Dict[str, Dict[str, int]]) -> bool:
    """Send success email when candidate passes with >70% score.
    Shows sections where they excelled.
    """
    try:
        smtp_server = os.environ.get("SMTP_SERVER", "")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER", "")
        smtp_password = os.environ.get("SMTP_PASSWORD", "")
        sender_email = os.environ.get("SMTP_FROM_EMAIL") or os.environ.get("SMTP_SENDER") or (smtp_user or "noreply@oaca.local")
        app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000")

        if not smtp_server or not smtp_user or not smtp_password:
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎉 OACA – Congratulations! You Passed the Quiz"
        msg['From'] = sender_email
        msg['To'] = target_email

        # Identify sections where candidate excelled (>80% score)
        excellent_sections = []
        good_sections = []
        for section_name, stats in per_section.items():
            attempted = stats.get("attempted", 0)
            correct_count = stats.get("correct", 0)
            if attempted > 0:
                section_percentage = (correct_count / attempted) * 100
                if section_percentage >= 80:
                    excellent_sections.append(f"{section_name} ({int(section_percentage)}%)")
                elif section_percentage >= 70:
                    good_sections.append(f"{section_name} ({int(section_percentage)}%)")

        # Build sections HTML
        sections_html = ""
        if excellent_sections:
            sections_html += f"""
            <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
              <h3 style="color: #22c55e; margin: 0 0 8px 0;">🌟 Excellent Performance (≥80%):</h3>
              <ul style="margin: 0; padding-left: 20px; color: #86efac;">
                {''.join(f'<li>{section}</li>' for section in excellent_sections)}
              </ul>
            </div>
            """
        if good_sections:
            sections_html += f"""
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
              <h3 style="color: #3b82f6; margin: 0 0 8px 0;">✅ Good Performance (≥70%):</h3>
              <ul style="margin: 0; padding-left: 20px; color: #93c5fd;">
                {''.join(f'<li>{section}</li>' for section in good_sections)}
              </ul>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>OACA Quiz Success</title>
        </head>
        <body style="font-family:Segoe UI,Roboto,Arial,sans-serif; margin:0; background:#0b1d44; color:#eaf2ff;">
          <div style="max-width:640px;margin:0 auto;padding:24px;">
            <div style="background:linear-gradient(135deg,#10265f,#0b1d44); border:1px solid rgba(255,255,255,0.15); border-radius:16px; overflow:hidden;">
              <div style="padding:22px 22px 8px; text-align:center;">
                <div style="width:56px;height:56px;margin:0 auto 10px; border-radius:14px; background:linear-gradient(135deg,#22c55e,#16a34a); display:flex; align-items:center; justify-content:center; font-weight:800; color:#fff; font-size:32px;">✓</div>
                <div style="font-size:22px; font-weight:800; letter-spacing:.2px;">OACA Aviation</div>
                <div style="opacity:.8; font-size:13px;">Aviation Administration System</div>
              </div>
              <div style="padding:16px 24px 6px;">
                <h2 style="margin:10px 0 8px; font-size:24px; color:#22c55e; text-align:center;">🎉 Congratulations!</h2>
                <p style="margin:0 0 12px; line-height:1.55; text-align:center; font-size:18px;">You have successfully passed the OACA aviation quiz!</p>
                
                <div style="background: rgba(59, 130, 246, 0.15); border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                  <div style="font-size:48px; font-weight:800; color:#60a5fa; margin-bottom:8px;">{int(percentage)}%</div>
                  <div style="font-size:16px; color:#cbd5e1;">Final Score: {correct}/{total} correct answers</div>
                </div>

                {sections_html}

                <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.35); border-radius: 8px; padding: 16px; margin: 20px 0;">
                  <h3 style="color: #86efac; margin: 0 0 8px 0;">✨ What's Next?</h3>
                  <p style="color: #bbf7d0; font-size: 14px; margin: 0;">Your results have been recorded. The OACA administration team will review your performance and contact you with next steps.</p>
                </div>

                <p style="margin:16px 0 22px; text-align:center;">
                  <a href="{app_base_url.rstrip('/')}/home" style="display:inline-block; padding:12px 18px; background:linear-gradient(135deg,#16a34a,#22c55e); color:#ffffff; text-decoration:none; border-radius:10px; font-weight:700; box-shadow:0 8px 20px rgba(34,197,94,.35);">View Dashboard</a>
                </p>
              </div>
              <div style="padding:16px 24px 22px; border-top:1px solid rgba(255,255,255,0.14); text-align:center; opacity:.8; font-size:12px;">
                © OACA Aviation. All rights reserved.
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
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send success email: {e}")
        return False


def _send_assignment_email_smtp(target_email: str, assignment_id: str, per_section: Dict[str, int]) -> bool:
    """Send assignment email using SMTP settings from environment.
    Env vars:
      SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_SENDER, APP_BASE_URL
    """
    try:
      smtp_server = os.environ.get("SMTP_SERVER", "")
      smtp_port = int(os.environ.get("SMTP_PORT", "587"))
      # Support both naming schemes (align with users.py / configuration.py)
      smtp_user = os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER", "")
      smtp_password = os.environ.get("SMTP_PASSWORD", "")
      sender_email = os.environ.get("SMTP_FROM_EMAIL") or os.environ.get("SMTP_SENDER") or (smtp_user or "noreply@oaca.local")
      app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000")

      if not smtp_server or not smtp_user or not smtp_password:
          # Incomplete SMTP configuration
          return False

      start_url = f"{app_base_url.rstrip('/')}/assigned_quiz.html?assignment_id={assignment_id}"

      msg = MIMEMultipart('alternative')
      msg['Subject'] = "OACA – New Quiz Assigned"
      msg['From'] = sender_email
      msg['To'] = target_email

      # OACA branded minimalist email (no section breakdown)
      html_content = f"""
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>OACA Quiz Assignment</title>
      </head>
      <body style=\"font-family:Segoe UI,Roboto,Arial,sans-serif; margin:0; background:#0b1d44; color:#eaf2ff;\">\n        <div style=\"max-width:640px;margin:0 auto;padding:24px;\">\n          <div style=\"background:linear-gradient(135deg,#10265f,#0b1d44); border:1px solid rgba(255,255,255,0.15); border-radius:16px; overflow:hidden;\">\n            <div style=\"padding:22px 22px 8px; text-align:center;\">\n              <div style=\"width:56px;height:56px;margin:0 auto 10px; border-radius:14px; background:linear-gradient(135deg,#3b82f6,#60a5fa); display:flex; align-items:center; justify-content:center; font-weight:800; color:#fff;\">✈</div>\n              <div style=\"font-size:22px; font-weight:800; letter-spacing:.2px;\">OACA Aviation</div>\n              <div style=\"opacity:.8; font-size:13px;\">Aviation Administration System</div>\n            </div>\n            <div style=\"padding:16px 24px 6px;\">\n              <h2 style=\"margin:10px 0 8px; font-size:20px;\">New Quiz Assigned</h2>\n              <p style=\"margin:0 0 12px; line-height:1.55;\">A new quiz has been assigned to your account. Click the button below to begin. Your progress will be timed.</p>\n              <p style=\"margin:16px 0 22px;\">\n                <a href=\"{start_url}\" style=\"display:inline-block; padding:12px 18px; background:linear-gradient(135deg,#274bcc,#3b82f6); color:#ffffff; text-decoration:none; border-radius:10px; font-weight:700; box-shadow:0 8px 20px rgba(30,64,175,.35);\">Start Quiz</a>\n              </p>\n              <div style=\"font-size:12px; color:#cfe2ff; opacity:.85;\">If the button doesn’t work, copy and paste this link:</div>\n              <div style=\"font-size:12px; margin-top:6px;\"><a href=\"{start_url}\" style=\"color:#93c5fd; text-decoration:none;\">{start_url}</a></div>\n            </div>\n            <div style=\"padding:16px 24px 22px; border-top:1px solid rgba(255,255,255,0.14); text-align:center; opacity:.8; font-size:12px;\">\n              © OACA Aviation. All rights reserved.\n            </div>\n          </div>\n        </div>\n      </body>\n      </html>\n      """
      msg.attach(MIMEText(html_content, 'html'))

      server = smtplib.SMTP(smtp_server, smtp_port)
      server.starttls()
      server.login(smtp_user, smtp_password)
      server.sendmail(sender_email, target_email, msg.as_string())
      server.quit()
      return True
    except Exception:
      return False



@scores_bp.route("/api/quiz-assignments", methods=["POST"])  # create assignment when user starts a quiz
def create_quiz_assignment():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    # If admin provides an explicit email and per-section counts, create an admin assignment for that user.
    # expected admin payload: { email: string, per_section: { section_name: int }, total: 15 }
    # Fallback (user self-start): { category: string|null, question_count: int }
    if body.get("email"):
        # admin create assignment for candidate (auto-generate 60 random questions across all sections)
        if claims.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        target_email = str(body.get("email")).strip().lower()
        
        db = get_db()
        raw_per_section = body.get("per_section")
        per_section: Dict[str, int] = {str(k): int(v) for k, v in (raw_per_section or {}).items() if int(v) > 0}
        
        # Delete any existing unfinished assignments for this user before creating new one
        db[ASSIGNMENTS_COLLECTION].delete_many({
            "email": target_email,
            "finished_at": None  # Only delete unfinished assignments
        })

        # Reset attempts for the user when assigning a new quiz (admin override)
        # This allows admins to reassign quizzes even if user cheated, was rejected, or failed
        now = datetime.datetime.utcnow()
        db[USER_ATTEMPTS_COLLECTION].update_one(
            {"email": target_email},
            {
                "$set": {
                    "email": target_email,
                    "attempts_used": 0,  # Reset attempts for new assignment
                    "passed": False,
                    "pass_date": None,
                    "final_score": None,
                    "last_attempt": None,
                    "updated_at": now
                }
            },
            upsert=True
        )

        # Load quiz data and build a global pool of questions {section, id}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Prefer v2 JSON if available
        data_path_v2 = os.path.join(base_dir, "aviation_quiz_data_v2.json")
        data_path_v1 = os.path.join(base_dir, "aviation_quiz_data.json")
        data_path = data_path_v2 if os.path.exists(data_path_v2) else data_path_v1
        try:
            with open(data_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            return jsonify({"error": f"failed to load quiz data: {e}"}), 500
        
        global_pool: List[Dict[str, Any]] = []  # {section, id}
        
        # Handle new format: exams[].activities[].questions[]
        if "exams" in data:
            for exam in data.get("exams", []):
                for activity in exam.get("activities", []):
                    section_name = activity.get("title", "Unknown")
                    for q in activity.get("questions", []):
                        if q.get("id") is not None:
                            global_pool.append({"section": section_name, "id": q.get("id")})
        # Handle old format: quiz_data.categories[].questions[]
        elif "quiz_data" in data:
            categories: List[Dict[str, Any]] = data.get("quiz_data", {}).get("categories", [])
            for cat in categories:
                nm = cat.get("name")
                if not nm:
                    continue
                for q in (cat.get("questions", []) or []):
                    if q.get("id") is not None:
                        global_pool.append({"section": nm, "id": q.get("id")})
        import random
        # Get total number of questions from request body (default 60, max 60)
        # For self-start, use question_count if provided, otherwise default to 60
        question_count = body.get("question_count")
        if question_count is not None:
            desired_total = min(max(int(question_count), 1), 60)
        else:
            desired_total = min(max(int(body.get("total", 60)), 1), 60)
        if len(global_pool) < desired_total:
            return jsonify({"error": f"Not enough questions in pool (need {desired_total}, have {len(global_pool)})"}), 400

        # Exclude questions used in previous assignments for this user when possible
        prev_used: set[tuple[str, int]] = set()
        try:
            prev_docs = list(db[ASSIGNMENTS_COLLECTION].find({"email": target_email}, {"selected": 1}))
            for doc_prev in prev_docs:
                for it in (doc_prev.get("selected") or []):
                    sec = str(it.get("section"))
                    qid = it.get("id")
                    if isinstance(qid, int) and sec:
                        prev_used.add((sec, qid))
        except Exception:
            prev_used = set()

        # Filter pool to unseen first
        unseen_pool = [q for q in global_pool if (q.get("section"), q.get("id")) not in prev_used]

        selected: list[dict] = []
        # Take as many unseen as possible
        if len(unseen_pool) >= desired_total:
            selected = random.sample(unseen_pool, desired_total)
        else:
            selected.extend(random.sample(unseen_pool, len(unseen_pool)))
            # Backfill from remaining pool without duplicating entries already chosen
            remaining_needed = desired_total - len(selected)
            remaining_pool = [q for q in global_pool if (q.get("section"), q.get("id")) not in {(x.get("section"), x.get("id")) for x in selected}]
            if len(remaining_pool) < remaining_needed:
                # If still not enough (shouldn't happen), just shuffle and take what we can
                random.shuffle(remaining_pool)
                selected.extend(remaining_pool[:remaining_needed])
            else:
                selected.extend(random.sample(remaining_pool, remaining_needed))

        # Randomize order to avoid same order each exam
        random.shuffle(selected)
        # Calculate duration using rule of three: 60 questions = 60 minutes (3600 seconds)
        # So: duration_seconds = (desired_total * 3600) / 60 = desired_total * 60
        duration_seconds = desired_total * 60  # 1 minute per question
        doc = {
            "email": target_email,
            "assigned_by": claims.get("email"),
            "per_section": None,
            "total": int(desired_total),
            "selected": selected,
            "created_at": datetime.datetime.utcnow(),
            "started_at": None,
            "finished_at": None,
            "duration_seconds": duration_seconds,
            "duration_used_seconds": None,
            "score": None,
            "total_with_keys": None,
            "attempted": None,
        }
        db = get_db()
        result = db[ASSIGNMENTS_COLLECTION].insert_one(doc)
        # Attempts are reset to 0 above, no need to increment here
        
        # Send notification email (SMTP if configured) and store notification
        try:
            # Attempt SMTP; if not configured, log to console as fallback
            sent = _send_assignment_email_smtp(target_email, str(result.inserted_id), (per_section or {}))
            if not sent:
                print(f"[ASSIGNMENT EMAIL - FALLBACK] To: {target_email} — You have been assigned a quiz with {int(desired_total)} questions. Start: /assigned_quiz.html?assignment_id={str(result.inserted_id)}")
            # Store notification for inbox
            db[NOTIFICATIONS_COLLECTION].insert_one({
                "email": target_email,
                "type": "quiz_assignment",
                "title": "New Quiz Assigned",
                "message": f"You have been assigned a quiz with {int(desired_total)} questions. Click to start.",
                "assignment_id": str(result.inserted_id),
                "created_at": datetime.datetime.utcnow(),
                "read": False,
            })
        except Exception:
            pass
        return jsonify({"ok": True, "assignment_id": str(result.inserted_id)})
    else:
        # self-start: create a full assignment for the current user with selected questions
        target_email = claims.get("email")
        db = get_db()
        # Check attempt limit
        attempt_record = db[USER_ATTEMPTS_COLLECTION].find_one({"email": target_email})
        attempts_used = attempt_record.get("attempts_used", 0) if attempt_record else 0
        if attempts_used >= 3:
            return jsonify({"error": "Maximum attempts (3) already used. You cannot take the quiz again."}), 400

        # Build global pool from quiz data
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path_v2 = os.path.join(base_dir, "aviation_quiz_data_v2.json")
        data_path_v1 = os.path.join(base_dir, "aviation_quiz_data.json")
        data_path = data_path_v2 if os.path.exists(data_path_v2) else data_path_v1
        try:
            with open(data_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            return jsonify({"error": f"failed to load quiz data: {e}"}), 500

        global_pool: List[Dict[str, Any]] = []  # {section, id}
        if "exams" in data:
            for exam in data.get("exams", []):
                for activity in exam.get("activities", []):
                    section_name = activity.get("title", "Unknown")
                    for q in activity.get("questions", []):
                        if q.get("id") is not None:
                            global_pool.append({"section": section_name, "id": q.get("id")})
        elif "quiz_data" in data:
            categories: List[Dict[str, Any]] = data.get("quiz_data", {}).get("categories", [])
            for cat in categories:
                nm = cat.get("name")
                if not nm:
                    continue
                for q in (cat.get("questions", []) or []):
                    if q.get("id") is not None:
                        global_pool.append({"section": nm, "id": q.get("id")})

        import random
        # Get total number of questions from request body (default 60, max 60)
        desired_total = min(max(int(body.get("total", 60)), 1), 60)
        if len(global_pool) < desired_total:
            return jsonify({"error": f"Not enough questions in pool (need {desired_total}, have {len(global_pool)})"}), 400

        # Avoid reusing previously used questions for this user
        prev_used: set[tuple[str, int]] = set()
        try:
            prev_docs = list(db[ASSIGNMENTS_COLLECTION].find({"email": target_email}, {"selected": 1}))
            for doc_prev in prev_docs:
                for it in (doc_prev.get("selected") or []):
                    sec = str(it.get("section"))
                    qid = it.get("id")
                    if isinstance(qid, int) and sec:
                        prev_used.add((sec, qid))
        except Exception:
            prev_used = set()

        unseen_pool = [q for q in global_pool if (q.get("section"), q.get("id")) not in prev_used]
        selected: List[Dict[str, Any]] = []
        if len(unseen_pool) >= desired_total:
            selected = random.sample(unseen_pool, desired_total)
        else:
            selected.extend(random.sample(unseen_pool, len(unseen_pool)))
            remaining_needed = desired_total - len(selected)
            remaining_pool = [q for q in global_pool if (q.get("section"), q.get("id")) not in {(x.get("section"), x.get("id")) for x in selected}]
            if len(remaining_pool) < remaining_needed:
                random.shuffle(remaining_pool)
                selected.extend(remaining_pool[:remaining_needed])
            else:
                selected.extend(random.sample(remaining_pool, remaining_needed))
        random.shuffle(selected)

        # Calculate duration using rule of three: 60 questions = 60 minutes (3600 seconds)
        # So: duration_seconds = (desired_total * 3600) / 60 = desired_total * 60
        duration_seconds = desired_total * 60  # 1 minute per question

        # Create assignment doc
        doc = {
            "email": target_email,
            "assigned_by": target_email,
            "per_section": None,
            "total": int(desired_total),
            "selected": selected,
            "created_at": datetime.datetime.utcnow(),
            "started_at": None,
            "finished_at": None,
            "duration_seconds": duration_seconds,
            "duration_used_seconds": None,
            "score": None,
            "total_with_keys": None,
            "attempted": None,
        }
        result = db[ASSIGNMENTS_COLLECTION].insert_one(doc)

        # Don't increment attempts here - wait until quiz actually starts
        # Attempts will be incremented when started_at is set in the questions endpoint
        return jsonify({"ok": True, "assignment_id": str(result.inserted_id)})


@scores_bp.route("/api/quiz-assignments", methods=["GET"])  # admin list assignments
def list_quiz_assignments():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    cursor = get_db()[ASSIGNMENTS_COLLECTION].find({}).sort("created_at", -1)
    out: List[Dict[str, Any]] = []
    for doc in cursor:
        d = dict(doc)
        if d.get("_id") is not None:
            d["assignment_id"] = str(d.pop("_id"))
        out.append(d)
    return jsonify(out)


@scores_bp.route("/api/quiz-sections", methods=["GET"])  # list available sections
def list_quiz_sections():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path_v2 = os.path.join(base_dir, "aviation_quiz_data_v2.json")
    data_path_v1 = os.path.join(base_dir, "aviation_quiz_data.json")
    data_path = data_path_v2 if os.path.exists(data_path_v2) else data_path_v1
    with open(data_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    # Handle new format: exams[].activities[].questions[]
    if "exams" in data:
        sections = []
        for exam in data.get("exams", []):
            for activity in exam.get("activities", []):
                section_name = activity.get("title", "Unknown")
                question_count = len(activity.get("questions", []))
                sections.append({"name": section_name, "count": question_count})
        return jsonify(sections)
    # Handle old format: quiz_data.categories[].questions[]
    elif "quiz_data" in data:
        categories: List[Dict[str, Any]] = data.get("quiz_data", {}).get("categories", [])
        return jsonify([{ "name": c.get("name"), "count": len(c.get("questions", []) or []) } for c in categories])
    else:
        return jsonify([])


@scores_bp.route("/api/my/assignments", methods=["GET"])  # user lists own assignments
def my_assignments():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    email = claims.get("email")
    cursor = get_db()[ASSIGNMENTS_COLLECTION].find({"email": email}).sort("created_at", -1)
    out: List[Dict[str, Any]] = []
    for doc in cursor:
        d = dict(doc)
        # Promote _id to assignment_id (string) for client convenience
        if d.get("_id") is not None:
            d["assignment_id"] = str(d.pop("_id"))
        out.append(d)
    return jsonify(out)

@scores_bp.route("/api/my/attempts", methods=["GET"])  # get user's attempts info
def get_my_attempts():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = claims.get("email")
    db = get_db()
    
    # Get attempt record
    attempt_record = db[USER_ATTEMPTS_COLLECTION].find_one({"email": email})
    attempts_used = attempt_record.get("attempts_used", 0) if attempt_record else 0
    passed = attempt_record.get("passed", False) if attempt_record else False
    final_score = attempt_record.get("final_score", None) if attempt_record else None
    
    return jsonify({
        "attempts_used": attempts_used,
        "remaining_attempts": max(0, 3 - attempts_used),
        "passed": passed,
        "final_score": final_score,
        "email": email
    })


@scores_bp.route("/api/my/test-history", methods=["GET"])  # get user's test history
def get_my_test_history():
    """Get user's completed test history with scores and details"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = claims.get("email")
    db = get_db()
    
    # Get all completed assignments for this user (finished_at is not None)
    cursor = db[ASSIGNMENTS_COLLECTION].find(
        {
            "email": email,
            "finished_at": {"$ne": None}
        }
    ).sort("finished_at", -1)  # Most recent first
    
    history: List[Dict[str, Any]] = []
    for doc in cursor:
        d = dict(doc)
        # Convert _id to string
        if d.get("_id") is not None:
            d["assignment_id"] = str(d.pop("_id"))
        
        # Format the assignment data for history display
        history_item = {
            "assignment_id": d.get("assignment_id"),
            "created_at": d.get("created_at"),
            "started_at": d.get("started_at"),
            "finished_at": d.get("finished_at"),
            "score": d.get("score", 0),
            "total_with_keys": d.get("total_with_keys", 0),
            "attempted": d.get("attempted", 0),
            "percentage_score": d.get("percentage_score", 0),
            "passed": d.get("passed", False),
            "terminated": d.get("terminated", False),
            "termination_reason": d.get("termination_reason"),
            "duration_used_seconds": d.get("duration_used_seconds"),
            "duration_seconds": d.get("duration_seconds", 15 * 60),
            "per_section": d.get("per_section", {}),
            "total": d.get("total", 0),
        }
        history.append(history_item)
    
    return jsonify(history)


@scores_bp.route("/api/quiz-assignments/questions", methods=["POST"])  # get questions for an assignment id
def get_assignment_questions():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    assignment_id = body.get("assignment_id")
    if not assignment_id:
        return jsonify({"error": "assignment_id required"}), 400
    from bson import ObjectId
    assignment = get_db()[ASSIGNMENTS_COLLECTION].find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        return jsonify({"error": "Not found"}), 404
    if claims.get("role") != "admin" and assignment.get("email") != claims.get("email"):
        return jsonify({"error": "Forbidden"}), 403
    # Expiry enforcement based on started_at + duration_seconds
    now = datetime.datetime.utcnow()
    duration = int(assignment.get("duration_seconds") or (15 * 60))
    started_at = assignment.get("started_at")
    finished_at = assignment.get("finished_at")

    expired = False
    if started_at and not finished_at:
        # If already started, check expiry
        elapsed = int((now - started_at).total_seconds())
        if elapsed >= duration:
            # Auto-finish on timeout but still allow viewing questions
            try:
                get_db()[ASSIGNMENTS_COLLECTION].update_one(
                    {"_id": assignment["_id"]},
                    {"$set": {
                        "finished_at": now,
                        "duration_used_seconds": duration,
                    }}
                )
            except Exception:
                pass
            expired = True

    # Load quiz data and materialize selected questions
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path_v2 = os.path.join(base_dir, "aviation_quiz_data_v2.json")
    data_path_v1 = os.path.join(base_dir, "aviation_quiz_data.json")
    data_path = data_path_v2 if os.path.exists(data_path_v2) else data_path_v1
    with open(data_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    
    section_to_qs: Dict[str, Dict[int, Dict[str, Any]]] = {}
    
    # Handle new format: exams[].activities[].questions[]
    if "exams" in data:
        for exam in data.get("exams", []):
            for activity in exam.get("activities", []):
                section_name = activity.get("title", "Unknown")
                idx: Dict[int, Dict[str, Any]] = {}
                for q in activity.get("questions", []):
                    if isinstance(q.get("id"), int):
                        # Convert answers array to options dict format for compatibility
                        q_copy = dict(q)
                        if "answers" in q_copy and isinstance(q_copy["answers"], list):
                            # Convert answers array to A, B, C, D options
                            options = {}
                            for i, answer in enumerate(q_copy["answers"]):
                                options[chr(65 + i)] = answer  # A, B, C, D
                            q_copy["options"] = options
                            # Set correct answer if not already set
                            if "correct_answer" not in q_copy:
                                q_copy["correct_answer"] = "A"  # Default to first answer
                        idx[int(q["id"])] = q_copy
                section_to_qs[section_name] = idx
    # Handle old format: quiz_data.categories[].questions[]
    elif "quiz_data" in data:
        categories: List[Dict[str, Any]] = data.get("quiz_data", {}).get("categories", [])
        for cat in categories:
            nm = cat.get("name")
            if not nm:
                continue
            idx: Dict[int, Dict[str, Any]] = {}
            for q in cat.get("questions", []) or []:
                if isinstance(q.get("id"), int):
                    idx[int(q["id"])] = q
            section_to_qs[nm] = idx
    result_questions: List[Dict[str, Any]] = []
    for item in assignment.get("selected", []) or []:
        sec = item.get("section")
        qid = item.get("id")
        q = (section_to_qs.get(sec) or {}).get(int(qid))
        if q:
            # include section meta so UIs can display source section
            q2 = dict(q)
            q2["_section"] = sec
            result_questions.append(q2)
    # Mark started_at if not set and count attempt
    if not assignment.get("started_at"):
        db = get_db()
        db[ASSIGNMENTS_COLLECTION].update_one({"_id": assignment["_id"]}, {"$set": {"started_at": now}})
        # Count attempt immediately when quiz starts
        email = assignment.get("email")
        if email:
            attempt_record = db[USER_ATTEMPTS_COLLECTION].find_one({"email": email})
            attempts_used = attempt_record.get("attempts_used", 0) if attempt_record else 0
            # Only increment if this assignment hasn't been counted yet
            if not assignment.get("attempt_counted", False) and attempts_used < 3:
                db[USER_ATTEMPTS_COLLECTION].update_one(
                    {"email": email},
                    {
                        "$set": {
                            "email": email,
                            "attempts_used": attempts_used + 1,
                            "last_attempt": now,
                            "updated_at": now
                        }
                    },
                    upsert=True
                )
                # Mark this assignment as counted
                db[ASSIGNMENTS_COLLECTION].update_one(
                    {"_id": assignment["_id"]},
                    {"$set": {"attempt_counted": True}}
                )
                # Notify admins that this candidate started the quiz (best-effort, non-blocking)
                try:
                    # local helper to avoid top-level side-effects
                    def _notify_admins_on_quiz_start(assignment_obj_id):
                        try:
                            smtp_server = os.environ.get("SMTP_SERVER", "")
                            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
                            smtp_user = os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER", "")
                            smtp_password = os.environ.get("SMTP_PASSWORD", "")
                            sender_email = os.environ.get("SMTP_FROM_EMAIL") or os.environ.get("SMTP_SENDER") or (smtp_user or "noreply@oaca.local")
                            if not smtp_server or not smtp_user or not smtp_password:
                                return False

                            db2 = get_db()
                            a = db2[ASSIGNMENTS_COLLECTION].find_one({"_id": assignment_obj_id})
                            if not a:
                                return False
                            candidate_email = a.get("email")
                            # resolve candidate display name if available
                            user = db2[USERS_COLLECTION].find_one({"email": candidate_email}, {"display_name": 1, "username": 1})
                            display_name = None
                            if user:
                                display_name = user.get("display_name") or user.get("username")
                            display_name = display_name or (candidate_email.split("@")[0] if candidate_email else "Unknown")

                            # get admin emails
                            admins_cursor = db2[USERS_COLLECTION].find({"role": "admin"}, {"email": 1})
                            admin_emails = [x.get("email") for x in admins_cursor if x.get("email")]
                            if not admin_emails:
                                return False

                            # build email HTML with embedded reference image if available
                            ref_img = a.get("reference_image")
                            start_url = f"{os.environ.get('APP_BASE_URL', 'http://localhost:8000').rstrip('/')}/assigned_quiz.html?assignment_id={str(a.get('_id'))}"
                            msg = MIMEMultipart('alternative')
                            msg['Subject'] = f"OACA – Quiz started by {display_name}"
                            msg['From'] = sender_email
                            msg['To'] = ','.join(admin_emails)
                            html = ""
                            html += "<div style='font-family:Segoe UI, Roboto, Arial, sans-serif; color:#0b1d44;'>"
                            html += "<h3>Quiz Started</h3>"
                            html += f"<p><strong>{display_name}</strong> ({candidate_email}) has started the quiz.</p>"
                            html += f"<p>Assignment: {str(a.get('_id'))}</p>"
                            html += f"<p><a href='{start_url}'>Open assignment</a></p>"
                            if ref_img:
                                html += f"<div style='margin-top:12px;'><img src='{ref_img}' alt='reference face' style='max-width:360px;border-radius:8px;border:1px solid #ccc;'></div>"
                            html += "</div>"
                            msg.attach(MIMEText(html, 'html'))

                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                            server.login(smtp_user, smtp_password)
                            server.sendmail(sender_email, admin_emails, msg.as_string())
                            server.quit()
                            return True
                        except Exception:
                            return False

                    try:
                        # call helper with the ObjectId value
                        from bson import ObjectId
                        _notify_admins_on_quiz_start(assignment["_id"])
                    except Exception:
                        pass
                except Exception:
                    pass
    return jsonify({
        "quiz_data": {
            "title": "Assigned Quiz",
            "description": None,
            "categories": [{"name": "Assigned", "description": "", "questions": result_questions}]
        },
        "expired": expired,
        "terminated": bool(assignment.get("terminated"))
    })


@scores_bp.route("/api/scores", methods=["POST"])  # user submits a score
def submit_score():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    # expected: { category: string|null, attempted: int, correct: int, total_with_keys: int, assignment_id?: string, answers?: [{id, section?, your, correct?}] }
    doc = {
        "email": claims.get("email"),
        "category": body.get("category"),
        "attempted": int(body.get("attempted", 0)),
        "correct": int(body.get("correct", 0)),
        "total_with_keys": int(body.get("total_with_keys", 0)),
        "created_at": datetime.datetime.utcnow(),
    }
    get_db()[SCORES_COLLECTION].insert_one(doc)
    
    # Calculate percentage score
    correct = int(body.get("correct", 0))
    total_with_keys = int(body.get("total_with_keys", 0))
    percentage_score = (correct / total_with_keys * 100) if total_with_keys > 0 else 0
    
    # best-effort: update assignment if provided
    try:
        assignment_id = body.get("assignment_id")
        if assignment_id:
            from bson import ObjectId  # local import to avoid hard dep if not used
            db = get_db()
            assignment = db[ASSIGNMENTS_COLLECTION].find_one({"_id": ObjectId(assignment_id)})
            now = datetime.datetime.utcnow()
            duration_used = None
            if assignment:
                started_at = assignment.get("started_at")
                duration_total = int(assignment.get("duration_seconds") or (15 * 60))
                if started_at:
                    elapsed = int((now - started_at).total_seconds())
                    duration_used = min(max(elapsed, 0), duration_total)
            # compute per-section report and persist submitted answers if provided
            answers = body.get("answers") or []
            per_section: Dict[str, Dict[str, int]] = {}
            detailed: List[Dict[str, Any]] = []
            try:
                for a in answers:
                    sec = str(a.get("section") or "Unknown")
                    your = (a.get("your") or "").upper()
                    corr = (a.get("correct") or None)
                    if isinstance(corr, str):
                        corr = corr.upper()
                    row = {
                        "id": a.get("id"),
                        "section": sec,
                        "your": your,
                        "correct": corr,
                        "is_correct": (corr is not None and your == corr),
                    }
                    detailed.append(row)
                    if sec not in per_section:
                        per_section[sec] = {"attempted": 0, "correct": 0}
                    per_section[sec]["attempted"] += 1
                    if row["is_correct"]:
                        per_section[sec]["correct"] += 1
            except Exception:
                # ignore malformed answers; proceed with basic score update
                detailed = []
                per_section = {}
            db[ASSIGNMENTS_COLLECTION].update_one(
                {"_id": ObjectId(assignment_id)},
                {"$set": {
                    "finished_at": now,
                    "duration_used_seconds": duration_used,
                    "score": int(body.get("correct", 0)),
                    "total_with_keys": int(body.get("total_with_keys", 0)),
                    "attempted": int(body.get("attempted", 0)),
                    "answers": detailed if detailed else None,
                    "per_section": per_section if per_section else None,
                    "percentage_score": percentage_score,
                    "passed": percentage_score > 70,
                }}
            )
            
            # Send success email if candidate passed (score > 70%)
            if percentage_score > 70 and per_section:
                try:
                    _send_success_email(claims.get("email"), correct, total_with_keys, percentage_score, per_section)
                except Exception as e:
                    print(f"Failed to send success email: {e}")
                
                # Mark user as successfully completed - set attempts to max (3) so they can't take quiz again
                try:
                    db[USER_ATTEMPTS_COLLECTION].update_one(
                        {"email": claims.get("email")},
                        {
                            "$set": {
                                "attempts_used": 3,  # Max out attempts
                                "passed": True,
                                "pass_date": now,
                                "final_score": percentage_score,
                                "updated_at": now
                            }
                        },
                        upsert=True
                    )
                except Exception as e:
                    print(f"Failed to update user attempts: {e}")
    except Exception:
        pass
    return jsonify({"ok": True})


@scores_bp.route("/api/quiz-assignments/status", methods=["POST"])  # get remaining time/status for an assignment
def assignment_status():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    assignment_id = body.get("assignment_id")
    if not assignment_id:
        return jsonify({"error": "assignment_id required"}), 400
    try:
        from bson import ObjectId
        db = get_db()
        a = db[ASSIGNMENTS_COLLECTION].find_one({"_id": ObjectId(assignment_id)})
        if not a:
            return jsonify({"error": "Not found"}), 404
        if claims.get("role") != "admin" and a.get("email") != claims.get("email"):
            return jsonify({"error": "Forbidden"}), 403
        
        # Check if assignment was terminated due to violation
        if a.get("terminated"):
            return jsonify({
                "terminated": True,
                "violation_type": a.get("termination_reason", "unknown"),
                "message": a.get("termination_message", "Quiz terminated due to violation"),
                "terminated_at": a.get("terminated_at"),
                "finished": True  # Mark as finished when terminated
            }), 410  # Gone
        
        now = datetime.datetime.utcnow()
        started_at = a.get("started_at")
        finished_at = a.get("finished_at")
        duration = int(a.get("duration_seconds") or (15 * 60))
        remaining = None
        if started_at and not finished_at:
            elapsed = int((now - started_at).total_seconds())
            remaining = max(duration - elapsed, 0)
            if remaining == 0:
                # finalize if not already
                try:
                    db[ASSIGNMENTS_COLLECTION].update_one(
                        {"_id": a["_id"]},
                        {"$set": {
                            "finished_at": now,
                            "duration_used_seconds": duration,
                        }}
                    )
                    finished_at = now
                except Exception:
                    pass
        return jsonify({
            "started": bool(started_at),
            "finished": bool(finished_at) or a.get("terminated", False),
            "terminated": a.get("terminated", False),
            "remaining_seconds": 0 if finished_at or a.get("terminated") else (remaining if remaining is not None else duration),
            "duration_seconds": duration,
            "started_at": started_at.isoformat() if started_at else None,
            "finished_at": finished_at.isoformat() if finished_at else (a.get("terminated_at").isoformat() if a.get("terminated_at") else None),
        })
    except Exception:
        return jsonify({"error": "Bad request"}), 400


@scores_bp.route("/api/scores", methods=["GET"])  # admin lists scores
def list_scores():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    cursor = get_db()[SCORES_COLLECTION].find({}, {"_id": 0}).sort("created_at", -1)
    return jsonify(list(cursor))


@scores_bp.route("/api/log-violation", methods=["POST"])  # log seat detection violations
def log_violation():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    assignment_id = body.get("assignment_id")
    violation_type = body.get("type", "unknown")
    timestamp = body.get("timestamp")
    message = body.get("message", "")
    captured_image = body.get("captured_image", "")
    
    if not assignment_id:
        return jsonify({"error": "assignment_id required"}), 400
    
    # Store violation log
    violation_doc = {
        "email": claims.get("email"),
        "assignment_id": assignment_id,
        "type": violation_type,
        "message": message,
        "timestamp": datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.datetime.utcnow(),
        "created_at": datetime.datetime.utcnow(),
        "captured_image": captured_image if captured_image else None,
    }
    
    # Try to update assignment with violation count and mark as terminated
    try:
        from bson import ObjectId
        db = get_db()
        
        # Check if this is a critical violation that should terminate the quiz
        critical_violations = ['no_face_detected', 'multiple_faces', 'face_mismatch', 'seat_movement', 'NO_FACE', 'MULTIPLE_FACES', 'FACE_MISMATCH', 'DISTANCE_CHANGE']
        # NO_FACE is always critical now (both with and without movement)
        is_critical = violation_type in critical_violations
        
        update_data = {
            "$inc": {"violations": 1}, 
            "$push": {"violation_log": violation_doc}
        }
        
        if is_critical:
            # Mark assignment as terminated
            update_data["$set"] = {
                "terminated": True,
                "termination_reason": violation_type,
                "termination_message": message,
                "terminated_at": datetime.datetime.utcnow(),
                "finished_at": datetime.datetime.utcnow()  # treat terminated as finished for reporting
            }
        
        db[ASSIGNMENTS_COLLECTION].update_one(
            {"_id": ObjectId(assignment_id)},
            update_data
        )
    except Exception:
        pass
    
    return jsonify({"ok": True})


# Global variables for face tracking (per assignment)
reference_faces = {}  # assignment_id -> reference_face
last_face_times = {}  # assignment_id -> timestamp
face_positions = {}   # assignment_id -> list of positions
multiple_face_start_times = {}  # assignment_id -> when multiple faces first detected

@scores_bp.route("/api/check-face-setup", methods=["POST"])  # check if face setup is complete
def check_face_setup():
    """Check if reference face has been set up for this assignment"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    assignment_id = body.get("assignment_id")
    
    if not assignment_id:
        return jsonify({"error": "assignment_id required"}), 400
    
    # Check if reference face exists for this assignment
    face_setup_complete = assignment_id in reference_faces and reference_faces[assignment_id] is not None
    
    return jsonify({
        "face_setup_complete": face_setup_complete,
        "assignment_id": assignment_id
    })


@scores_bp.route("/api/setup-reference", methods=["POST"])  # setup reference face for comparison
def setup_reference():
    """Store reference face for comparison"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    image_data = body.get("image")
    assignment_id = body.get("assignment_id")
    
    print(f"Setup reference called for assignment: {assignment_id}")
    
    if not image_data:
        print("No image data provided")
        return jsonify({"error": "image required"}), 400
    
    try:
        import base64
        import cv2
        import numpy as np
        import time
        
        print("OpenCV imported successfully")
        
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode image")
            return jsonify({"error": "Invalid image"}), 400
        
        print(f"Image decoded successfully: {img.shape}")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load OpenCV's pre-trained face detection model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if face_cascade.empty():
            print("Failed to load face cascade classifier")
            return jsonify({'success': False, 'error': 'Face detection model not available'})
        
        print("Face cascade loaded successfully")
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        print(f"Detected {len(faces)} faces")
        
        if len(faces) == 0:
            print("No faces detected")
            return jsonify({'success': False, 'error': 'No face detected. Please ensure your face is clearly visible in the camera.'})
        
        if len(faces) > 1:
            print(f"Multiple faces detected: {len(faces)}")
            return jsonify({'success': False, 'error': f'Multiple faces detected ({len(faces)}). Please ensure only your face is visible.'})
        
        # Store reference face region with enhanced validation
        x, y, w, h = faces[0]
        reference_face = gray[y:y+h, x:x+w]
        print(f"Reference face stored: {reference_face.shape}")
        
        # Validate face quality
        face_area = w * h
        total_area = img.shape[0] * img.shape[1]
        face_ratio = face_area / total_area
        
        if face_ratio < 0.05:  # Face too small
            return jsonify({'success': False, 'error': 'Face too small. Please move closer to the camera.'})
        elif face_ratio > 0.3:  # Face too large
            return jsonify({'success': False, 'error': 'Face too large. Please move away from the camera.'})
        
        # Check face brightness/contrast
        mean_brightness = np.mean(reference_face)
        if mean_brightness < 50:  # Too dark
            return jsonify({'success': False, 'error': 'Face too dark. Please improve lighting.'})
        elif mean_brightness > 200:  # Too bright
            return jsonify({'success': False, 'error': 'Face too bright. Please adjust lighting.'})
        
        # Initialize tracking variables for this assignment
        if assignment_id:
            reference_faces[assignment_id] = reference_face
            last_face_times[assignment_id] = time.time()
            face_positions[assignment_id] = []
            print(f"Reference face captured and tracking initialized for assignment: {assignment_id}")
            print(f"Face quality - Ratio: {face_ratio:.3f}, Brightness: {mean_brightness:.1f}")
            # Persist original captured image (base64 data URL) to assignment for later reference/email
            try:
                from bson import ObjectId
                db = get_db()
                db[ASSIGNMENTS_COLLECTION].update_one(
                    {"_id": ObjectId(assignment_id)},
                    {"$set": {"reference_image": image_data}}
                )
            except Exception:
                pass
        
        return jsonify({'success': True, 'message': 'Reference face captured successfully'})
        
    except ImportError as e:
        print(f"OpenCV import error: {e}")
        # OpenCV not available, return success for testing
        return jsonify({'success': True, 'warning': 'OpenCV not available - face detection disabled'})
    except Exception as e:
        print(f"Setup reference error: {e}")
        return jsonify({'success': False, 'error': f'Face detection failed: {str(e)}'})


@scores_bp.route("/api/check-frame", methods=["POST"])  # face detection and monitoring
def check_frame():
    """Analyze frame for face detection and cheating detection"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    image_data = body.get("image")
    assignment_id = body.get("assignment_id")
    
    if not image_data:
        return jsonify({"error": "image required"}), 400
    
    try:
        import base64
        import cv2
        import numpy as np
        import time
        from datetime import datetime
        from bson import ObjectId
        
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"error": "Invalid image"}), 400
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load OpenCV's pre-trained face detection model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        face_count = len(faces)
        
        alerts = []
        current_time = time.time()
        
        # Initialize tracking variables for this assignment
        if assignment_id not in reference_faces:
            reference_faces[assignment_id] = None
            last_face_times[assignment_id] = None
            face_positions[assignment_id] = []

        # Attempts are now counted immediately when quiz starts in the questions endpoint
        
        # Check 1: No face detected - wait 15 seconds before rejecting (more lenient)
        if face_count == 0:
            if last_face_times[assignment_id] and (current_time - last_face_times[assignment_id]) > 15:
                # Check if movement was detected before no face
                movement_key = f"{assignment_id}_movement"
                if movement_key in multiple_face_start_times:
                    # Movement + no face for 15s = REJECT (potential cheating)
                    alert = {
                        'type': 'NO_FACE',
                        'message': 'No face detected for more than 15 seconds after movement - rejecting',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    }
                    alerts.append(alert)
                else:
                    # Just no face without movement - wait 15 seconds then reject
                    alert = {
                        'type': 'NO_FACE',
                        'message': 'No face detected for more than 15 seconds - rejecting',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    }
                    alerts.append(alert)
        else:
            last_face_times[assignment_id] = current_time
            
            # Reset movement timer when face is detected again
            movement_key = f"{assignment_id}_movement"
            if movement_key in multiple_face_start_times:
                del multiple_face_start_times[movement_key]
            
            # Check 2: Multiple faces - wait 10 seconds before rejection
            if face_count > 1:
                # Check if multiple faces detected for more than 10 seconds
                if assignment_id not in multiple_face_start_times:
                    multiple_face_start_times[assignment_id] = current_time
                elif (current_time - multiple_face_start_times[assignment_id]) > 10:
                    alert = {
                        'type': 'MULTIPLE_FACES',
                        'message': f'{face_count} faces detected for more than 10 seconds - rejecting',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    }
                    alerts.append(alert)
            else:
                # Reset multiple face timer if only one face detected
                if assignment_id in multiple_face_start_times:
                    del multiple_face_start_times[assignment_id]
            
            # Check 3: Face position change (standing up detection)
            x, y, w, h = faces[0]
            face_center_y = y + h/2
            img_height = img.shape[0]
            face_position_ratio = face_center_y / img_height
            
            face_positions[assignment_id].append(face_position_ratio)
            if len(face_positions[assignment_id]) > 30:  # Keep last 30 frames
                face_positions[assignment_id].pop(0)
            
            if len(face_positions[assignment_id]) >= 10:
                avg_position = np.mean(face_positions[assignment_id][-10:])
                if abs(face_position_ratio - avg_position) > 0.3:
                    # Movement detected - just alert, don't reject yet
                    alert = {
                        'type': 'POSITION_CHANGE',
                        'message': 'Significant position change detected - possible movement',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'low'
                    }
                    alerts.append(alert)
                    
                    # Start tracking movement + no face combination
                    movement_key = f"{assignment_id}_movement"
                    if movement_key not in multiple_face_start_times:
                        multiple_face_start_times[movement_key] = current_time
                else:
                    # Reset movement timer if position is normal
                    movement_key = f"{assignment_id}_movement"
                    if movement_key in multiple_face_start_times:
                        del multiple_face_start_times[movement_key]
            
            # Check 4: Face size change (moving away/closer)
            face_size_ratio = (w * h) / (img.shape[0] * img.shape[1])
            if face_size_ratio < 0.02:  # Face too small - moved away
                # Check if distance change detected for more than 10 seconds
                distance_key = f"{assignment_id}_distance_small"
                if distance_key not in multiple_face_start_times:
                    multiple_face_start_times[distance_key] = current_time
                elif (current_time - multiple_face_start_times[distance_key]) > 10:
                    alert = {
                        'type': 'DISTANCE_CHANGE',
                        'message': 'Student moved too far from camera for more than 10 seconds',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'medium'
                    }
                    alerts.append(alert)
            elif face_size_ratio > 0.15:  # Face too large - too close
                # Check if distance change detected for more than 10 seconds
                distance_key = f"{assignment_id}_distance_large"
                if distance_key not in multiple_face_start_times:
                    multiple_face_start_times[distance_key] = current_time
                elif (current_time - multiple_face_start_times[distance_key]) > 10:
                    alert = {
                        'type': 'DISTANCE_CHANGE',
                        'message': 'Student moved too close to camera for more than 10 seconds',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'low'
                    }
                    alerts.append(alert)
            else:
                # Reset distance change timers if face size is normal
                distance_key_small = f"{assignment_id}_distance_small"
                distance_key_large = f"{assignment_id}_distance_large"
                if distance_key_small in multiple_face_start_times:
                    del multiple_face_start_times[distance_key_small]
                if distance_key_large in multiple_face_start_times:
                    del multiple_face_start_times[distance_key_large]
            
            # Check 5: Face comparison (person switching) - Enhanced detection
            if reference_faces[assignment_id] is not None:
                current_face = gray[y:y+h, x:x+w]
                
                # Resize to same size for comparison
                try:
                    current_face_resized = cv2.resize(current_face, (reference_faces[assignment_id].shape[1], reference_faces[assignment_id].shape[0]))
                    
                    # Multiple similarity checks for better accuracy
                    # 1. Histogram comparison
                    hist_ref = cv2.calcHist([reference_faces[assignment_id]], [0], None, [256], [0, 256])
                    hist_cur = cv2.calcHist([current_face_resized], [0], None, [256], [0, 256])
                    hist_similarity = cv2.compareHist(hist_ref, hist_cur, cv2.HISTCMP_CORREL)
                    
                    # 2. Template matching
                    result = cv2.matchTemplate(current_face_resized, reference_faces[assignment_id], cv2.TM_CCOEFF_NORMED)
                    template_similarity = np.max(result)
                    
                    # 3. Structural similarity (SSIM-like)
                    # Resize both to same small size for structural comparison
                    ref_small = cv2.resize(reference_faces[assignment_id], (64, 64))
                    cur_small = cv2.resize(current_face_resized, (64, 64))
                    
                    # Calculate mean squared error
                    mse = np.mean((ref_small.astype("float") - cur_small.astype("float")) ** 2)
                    ssim_similarity = 1 - (mse / (255 ** 2))  # Normalize to 0-1
                    
                    # Combined similarity score (weighted average)
                    combined_similarity = (hist_similarity * 0.4 + template_similarity * 0.4 + ssim_similarity * 0.2)
                    
                    print(f"Face similarity check - Hist: {hist_similarity:.3f}, Template: {template_similarity:.3f}, SSIM: {ssim_similarity:.3f}, Combined: {combined_similarity:.3f}")
                    
                    # More strict threshold for face matching - wait 10 seconds before rejection
                    if combined_similarity < 0.7:  # Increased from 0.6 to 0.7 for stricter matching
                        # Check if face mismatch detected for more than 10 seconds
                        mismatch_key = f"{assignment_id}_mismatch"
                        if mismatch_key not in multiple_face_start_times:
                            multiple_face_start_times[mismatch_key] = current_time
                        elif (current_time - multiple_face_start_times[mismatch_key]) > 10:
                            alert = {
                                'type': 'FACE_MISMATCH',
                                'message': f'Different person detected (similarity: {combined_similarity:.2f}) for more than 10 seconds - rejecting',
                                'timestamp': datetime.now().isoformat(),
                                'severity': 'critical'
                            }
                            alerts.append(alert)
                            
                            # Log the violation
                            print(f"FACE MISMATCH DETECTED: Similarity {combined_similarity:.3f} below threshold 0.7 - REJECTING USER")
                    else:
                        # Reset face mismatch timer if face matches
                        mismatch_key = f"{assignment_id}_mismatch"
                        if mismatch_key in multiple_face_start_times:
                            del multiple_face_start_times[mismatch_key]
                        
                except Exception as e:
                    print(f"Face comparison error: {e}")
                    # If comparison fails, assume potential mismatch
                    alert = {
                        'type': 'FACE_MISMATCH',
                        'message': 'Face comparison failed - possible person switch',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    }
                    alerts.append(alert)
            else:
                # Set reference face on first detection
                reference_faces[assignment_id] = gray[y:y+h, x:x+w]
                print(f"Reference face set for assignment {assignment_id}")
            
            # Check 6: Eye detection within face region
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            
            if len(eyes) == 0:
                alert = {
                    'type': 'NO_EYES',
                    'message': 'Eyes not detected - face may be obscured',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'medium'
                }
                alerts.append(alert)
            elif len(eyes) > 2:
                alert = {
                    'type': 'MULTIPLE_EYES',
                    'message': 'Multiple eye pairs detected - possible cheating',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'high'
                }
                alerts.append(alert)
        
        return jsonify({
            'success': True,
            'faces_detected': face_count,
            'alerts': alerts
        })
        
    except ImportError:
        # OpenCV not available, return basic response
        return jsonify({
            'success': True,
            'faces_detected': 1,  # Assume face is present
            'alerts': []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/violation-reports", methods=["GET"])  # get violation reports for dashboard
def get_violation_reports():
    """Get violation reports for admin dashboard"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check if user is admin
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        db = get_db()
        
        # Get all assignments with violations or terminated
        assignments = list(db[ASSIGNMENTS_COLLECTION].find(
            {"$or": [
                {"violations": {"$gt": 0}},
                {"terminated": True}
            ]},
            {"violation_log": 1, "email": 1, "created_at": 1, "finished_at": 1, "violations": 1, "terminated": 1, "termination_reason": 1, "termination_message": 1, "terminated_at": 1}
        ).sort("created_at", -1))
        
        reports = []
        for assignment in assignments:
            violation_log = assignment.get("violation_log", [])
            is_terminated = assignment.get("terminated", False)
            
            # Include terminated assignments even without violation log
            if violation_log or is_terminated:
                # Group violations by assignment
                assignment_report = {
                    "assignment_id": str(assignment["_id"]),
                    "email": assignment.get("email"),
                    "created_at": assignment.get("created_at"),
                    "finished_at": assignment.get("finished_at"),
                    "terminated": is_terminated,
                    "termination_reason": assignment.get("termination_reason"),
                    "termination_message": assignment.get("termination_message"),
                    "terminated_at": assignment.get("terminated_at"),
                    "total_violations": assignment.get("violations", 0),
                    "violations": []
                }
                
                assignment_id_str = str(assignment["_id"])
                
                for violation in violation_log:
                    # Use assignment_id from violation if available, otherwise use parent assignment_id
                    violation_assignment_id = violation.get("assignment_id") or assignment_id_str
                    violation_info = {
                        "assignment_id": violation_assignment_id,  # Link violation to specific quiz/test
                        "type": violation.get("type"),
                        "message": violation.get("message"),
                        "timestamp": violation.get("timestamp"),
                        "has_image": bool(violation.get("captured_image"))
                    }
                    assignment_report["violations"].append(violation_info)
                
                # Add synthetic violation for terminated assignments without violation log
                if is_terminated and not violation_log:
                    synthetic_violation = {
                        "assignment_id": assignment_id_str,  # Link violation to specific quiz/test
                        "type": assignment.get("termination_reason", "UNKNOWN_VIOLATION"),
                        "message": assignment.get("termination_message", "Quiz terminated due to violation"),
                        "timestamp": assignment.get("terminated_at", assignment.get("created_at")),
                        "has_image": False
                    }
                    assignment_report["violations"].append(synthetic_violation)
                
                reports.append(assignment_report)
        
        return jsonify({"reports": reports})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/stats/success-rate", methods=["GET"])  # get overall success rate (public)
def get_success_rate():
    """Calculate success rate as percentage of users who passed (score > 70%) - Public endpoint"""
    try:
        db = get_db()
        
        # Count total users who completed the quiz (have a finished assignment)
        total_completed = db[ASSIGNMENTS_COLLECTION].count_documents({
            "finished_at": {"$ne": None},
            "terminated": {"$ne": True}  # Don't count terminated assignments
        })
        
        # Count users who passed (score > 70%)
        passed = db[ASSIGNMENTS_COLLECTION].count_documents({
            "finished_at": {"$ne": None},
            "terminated": {"$ne": True},
            "passed": True
        })
        
        success_rate = (passed / total_completed * 100) if total_completed > 0 else 0
        
        return jsonify({
            "success_rate": round(success_rate, 1),
            "total_completed": total_completed,
            "passed": passed,
            "failed": total_completed - passed
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/stats/dashboard", methods=["GET"])  # get dashboard stats (public)
def get_dashboard_stats():
    """Get dashboard statistics including total users registered, tests passed, and best score - Public endpoint"""
    try:
        db = get_db()
        
        # Count total users registered (all users, not just last month)
        total_users = db[USERS_COLLECTION].count_documents({})
        
        # Count tests passed (assignments that were finished successfully with passed=True)
        tests_passed = db[ASSIGNMENTS_COLLECTION].count_documents({
            "finished_at": {"$ne": None},
            "terminated": {"$ne": True},
            "passed": True
        })
        
        # Get best score rate (highest percentage_score)
        best_assignment = db[ASSIGNMENTS_COLLECTION].find_one(
            {
                "finished_at": {"$ne": None},
                "terminated": {"$ne": True},
                "percentage_score": {"$ne": None}
            },
            sort=[("percentage_score", -1)]
        )
        
        best_score_rate = 0
        if best_assignment and best_assignment.get("percentage_score") is not None:
            best_score_rate = round(float(best_assignment.get("percentage_score")), 1)
        
        return jsonify({
            "total_users": total_users,
            "tests_passed": tests_passed,
            "best_score_rate": best_score_rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/stats/top-scores", methods=["GET"])  # get top 5 best scores (public)
def get_top_scores():
    """Get top 5 best scores from all users - Public endpoint"""
    try:
        db = get_db()
        
        # Get top 5 assignments by percentage_score
        top_assignments = list(db[ASSIGNMENTS_COLLECTION].find(
            {
                "finished_at": {"$ne": None},
                "terminated": {"$ne": True},
                "percentage_score": {"$ne": None}
            },
            {
                "email": 1,
                "percentage_score": 1,
                "score": 1,
                "total_with_keys": 1,
                "finished_at": 1
            }
        ).sort("percentage_score", -1).limit(5))
        
        top_scores = []
        for assignment in top_assignments:
            email = assignment.get("email", "Unknown")
            # Get user display name if available
            user = db[USERS_COLLECTION].find_one({"email": email}, {"display_name": 1, "username": 1})
            display_name = None
            if user:
                display_name = user.get("display_name") or user.get("username")
            
            top_scores.append({
                "email": email,
                "display_name": display_name or email.split("@")[0],
                "percentage_score": round(float(assignment.get("percentage_score", 0)), 1),
                "score": assignment.get("score", 0),
                "total": assignment.get("total_with_keys", 0),
                "finished_at": assignment.get("finished_at")
            })
        
        return jsonify({"top_scores": top_scores})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/stats/most-asked", methods=["GET"])  # get most asked questions and sections (public)
def get_most_asked():
    """Get most asked questions and sections - Public endpoint"""
    try:
        db = get_db()
        
        # Get all finished assignments with selected questions
        assignments = list(db[ASSIGNMENTS_COLLECTION].find(
            {
                "finished_at": {"$ne": None},
                "selected": {"$exists": True, "$ne": None}
            },
            {"selected": 1}
        ))
        
        # Count question occurrences
        question_counts = {}  # {(section, question_id): count}
        section_counts = {}  # {section: count}
        
        for assignment in assignments:
            selected = assignment.get("selected", [])
            if not selected:
                continue
            
            for item in selected:
                section = item.get("section")
                question_id = item.get("id")
                
                if section and question_id is not None:
                    # Count question
                    key = (str(section), int(question_id))
                    question_counts[key] = question_counts.get(key, 0) + 1
                    
                    # Count section
                    section_counts[str(section)] = section_counts.get(str(section), 0) + 1
        
        # Get top 5 most asked questions
        top_questions = sorted(question_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_asked_questions = []
        for (section, qid), count in top_questions:
            most_asked_questions.append({
                "section": section,
                "question_id": qid,
                "count": count
            })
        
        # Get top 5 most asked sections
        top_sections = sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_asked_sections = []
        for section, count in top_sections:
            most_asked_sections.append({
                "section": section,
                "count": count
            })
        
        return jsonify({
            "most_asked_questions": most_asked_questions,
            "most_asked_sections": most_asked_sections
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/stats/airport-report", methods=["GET"])  # get aggregated report for an airport (admin)
def get_airport_report():
    """Return aggregated metrics (averages, pass rate, totals) for all users in a given airport"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    # Only admin can request airport-wide aggregated report
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    airport = request.args.get("airport") or ""
    try:
        db = get_db()
        # Find users assigned to the airport
        users_cursor = db[USERS_COLLECTION].find({"airport": airport}, {"email": 1})
        emails = [u.get("email") for u in users_cursor if u.get("email")]

        # If no users found, still return zeros
        if not emails:
            # Return empty metrics with count of users = 0
            return jsonify({
                "airport": airport,
                "total_users": 0,
                "total_completed": 0,
                "avg_percentage_score": None,
                "avg_score": None,
                "avg_attempts_used": None,
                "pass_rate": None
            })

        # Query finished, non-terminated assignments for these users
        cursor = db[ASSIGNMENTS_COLLECTION].find({
            "email": {"$in": emails},
            "finished_at": {"$ne": None},
            "terminated": {"$ne": True}
        }, {"percentage_score": 1, "score": 1, "attempted": 1})

        total_completed = 0
        sum_percentage = 0.0
        sum_score = 0.0
        sum_attempted = 0
        passed_count = 0
        for a in cursor:
            total_completed += 1
            pct = a.get("percentage_score")
            if pct is not None:
                try:
                    sum_percentage += float(pct)
                except Exception:
                    pass
            sc = a.get("score")
            if isinstance(sc, (int, float)):
                sum_score += float(sc)
            att = a.get("attempted")
            if isinstance(att, int):
                sum_attempted += att
            # determine pass by percentage if present
            if pct is not None:
                try:
                    if float(pct) > 70:
                        passed_count += 1
                except Exception:
                    pass

        # Compute averages
        avg_percentage = round(sum_percentage / total_completed, 2) if total_completed > 0 else None
        avg_score = round(sum_score / total_completed, 2) if total_completed > 0 else None
        avg_attempts = round(sum_attempted / total_completed, 2) if total_completed > 0 else None
        pass_rate = round((passed_count / total_completed) * 100, 2) if total_completed > 0 else None

        # Also return number of registered users for airport (including those without completed assignments)
        total_users = len(emails)

        return jsonify({
            "airport": airport,
            "total_users": total_users,
            "total_completed": total_completed,
            "avg_percentage_score": avg_percentage,
            "avg_score": avg_score,
            "avg_attempts_used": avg_attempts,
            "pass_rate": pass_rate,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@scores_bp.route("/api/violation-image/<assignment_id>/<int:violation_index>", methods=["GET"])  # get violation image
def get_violation_image(assignment_id, violation_index):
    """Get captured image for a specific violation"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check if user is admin
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        from bson import ObjectId
        db = get_db()
        
        assignment = db[ASSIGNMENTS_COLLECTION].find_one(
            {"_id": ObjectId(assignment_id)},
            {"violation_log": 1}
        )
        
        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404
        
        violation_log = assignment.get("violation_log", [])
        if violation_index >= len(violation_log):
            return jsonify({"error": "Violation not found"}), 404
        
        violation = violation_log[violation_index]
        captured_image = violation.get("captured_image")
        
        if not captured_image:
            return jsonify({"error": "No image available"}), 404
        
        # Return the base64 image data
        return jsonify({"image": captured_image})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


