import datetime
from typing import Any, Dict, List
import os
import json

from flask import Blueprint, jsonify, request

from configuration import get_db, SCORES_COLLECTION, USERS_COLLECTION, ASSIGNMENTS_COLLECTION, NOTIFICATIONS_COLLECTION
from login import _current_user_claims


scores_bp = Blueprint("scores", __name__)


@scores_bp.route("/api/quiz-assignments", methods=["POST"])  # create assignment when user starts a quiz
def create_quiz_assignment():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    # If admin provides an explicit email and per-section counts, create an admin assignment for that user.
    # expected admin payload: { email: string, per_section: { section_name: int }, total: 15 }
    # Fallback (user self-start): { category: string|null, question_count: int }
    if body.get("email") and isinstance(body.get("per_section"), dict):
        # admin create assignment for candidate
        if claims.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        target_email = str(body.get("email")).strip().lower()
        per_section: Dict[str, int] = {str(k): int(v) for k, v in body.get("per_section", {}).items()}
        total = int(body.get("total", 0))
        if total != 15:
            return jsonify({"error": "total must be 15"}), 400
        if sum(per_section.values()) != 15:
            return jsonify({"error": "per_section counts must sum to 15"}), 400
        # Load quiz data and select questions per section
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "aviation_quiz_data.json")
        try:
            with open(data_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            return jsonify({"error": f"failed to load quiz data: {e}"}), 500
        categories: List[Dict[str, Any]] = (data or {}).get("quiz_data", {}).get("categories", [])
        name_to_questions: Dict[str, List[Dict[str, Any]]] = {}
        for cat in categories:
            nm = cat.get("name")
            if not nm:
                continue
            qs = cat.get("questions", []) or []
            name_to_questions[nm] = list(qs)
        # Select question IDs
        import random
        selected: List[Dict[str, Any]] = []  # {section, id}
        for section_name, count in per_section.items():
            pool = name_to_questions.get(section_name, [])
            if len(pool) < count:
                return jsonify({"error": f"Not enough questions in section '{section_name}' (need {count}, have {len(pool)})"}), 400
            picks = random.sample(pool, count)
            for q in picks:
                selected.append({"section": section_name, "id": q.get("id")})
        doc = {
            "email": target_email,
            "assigned_by": claims.get("email"),
            "per_section": per_section,
            "total": 15,
            "selected": selected,
            "created_at": datetime.datetime.utcnow(),
            "started_at": None,
            "finished_at": None,
            "score": None,
            "total_with_keys": None,
            "attempted": None,
        }
        db = get_db()
        result = db[ASSIGNMENTS_COLLECTION].insert_one(doc)
        # Send notification email (mock) and store notification
        try:
            print(f"[ASSIGNMENT EMAIL] To: {target_email} — You have been assigned a quiz with 15 questions. Sections: {', '.join(f'{k}:{v}' for k,v in per_section.items())}")
            db[NOTIFICATIONS_COLLECTION].insert_one({
                "email": target_email,
                "type": "quiz_assignment",
                "title": "New Quiz Assigned",
                "message": f"You have been assigned a quiz with 15 questions.",
                "assignment_id": str(result.inserted_id),
                "created_at": datetime.datetime.utcnow(),
                "read": False,
            })
        except Exception:
            pass
        return jsonify({"ok": True, "assignment_id": str(result.inserted_id)})
    else:
        # self-start fallback
        doc = {
            "email": claims.get("email"),
            "category": body.get("category"),
            "question_count": int(body.get("question_count", 0)) or None,
            "started_at": datetime.datetime.utcnow(),
            "finished_at": None,
            "score": None,
            "total_with_keys": None,
            "attempted": None,
        }
        result = get_db()[ASSIGNMENTS_COLLECTION].insert_one(doc)
        return jsonify({"ok": True, "assignment_id": str(result.inserted_id)})


@scores_bp.route("/api/quiz-assignments", methods=["GET"])  # admin list assignments
def list_quiz_assignments():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    cursor = get_db()[ASSIGNMENTS_COLLECTION].find({}, {"_id": 0}).sort("started_at", -1)
    return jsonify(list(cursor))


@scores_bp.route("/api/quiz-sections", methods=["GET"])  # list available sections
def list_quiz_sections():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "aviation_quiz_data.json")
    with open(data_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    categories: List[Dict[str, Any]] = (data or {}).get("quiz_data", {}).get("categories", [])
    return jsonify([{ "name": c.get("name"), "count": len(c.get("questions", []) or []) } for c in categories])


@scores_bp.route("/api/my/assignments", methods=["GET"])  # user lists own assignments
def my_assignments():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    email = claims.get("email")
    cursor = get_db()[ASSIGNMENTS_COLLECTION].find({"email": email}, {"_id": 0}).sort("created_at", -1)
    return jsonify(list(cursor))


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
    # Load quiz data and materialize selected questions
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "aviation_quiz_data.json")
    with open(data_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    categories: List[Dict[str, Any]] = (data or {}).get("quiz_data", {}).get("categories", [])
    section_to_qs: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for cat in categories:
        nm = cat.get("name")
        if not nm:
            continue
        idx: Dict[int, Dict[str, Any]] = {}
        for q in cat.get("questions", []) or []:
            if isinstance(q.get("id"), int):
                idx[int(q["id"]) ] = q
        section_to_qs[nm] = idx
    result_questions: List[Dict[str, Any]] = []
    for item in assignment.get("selected", []) or []:
        sec = item.get("section")
        qid = item.get("id")
        q = (section_to_qs.get(sec) or {}).get(int(qid))
        if q:
            result_questions.append(q)
    # Mark started_at if not set
    if not assignment.get("started_at"):
        get_db()[ASSIGNMENTS_COLLECTION].update_one({"_id": assignment["_id"]}, {"$set": {"started_at": datetime.datetime.utcnow()}})
    return jsonify({"quiz_data": {"title": "Assigned Quiz", "description": None, "categories": [{"name": "Assigned", "description": "", "questions": result_questions}]}})


@scores_bp.route("/api/scores", methods=["POST"])  # user submits a score
def submit_score():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    body: Dict[str, Any] = request.get_json(silent=True) or {}
    # expected: { category: string|null, attempted: int, correct: int, total_with_keys: int, assignment_id?: string }
    doc = {
        "email": claims.get("email"),
        "category": body.get("category"),
        "attempted": int(body.get("attempted", 0)),
        "correct": int(body.get("correct", 0)),
        "total_with_keys": int(body.get("total_with_keys", 0)),
        "created_at": datetime.datetime.utcnow(),
    }
    get_db()[SCORES_COLLECTION].insert_one(doc)
    # best-effort: update assignment if provided
    try:
        assignment_id = body.get("assignment_id")
        if assignment_id:
            from bson import ObjectId  # local import to avoid hard dep if not used
            get_db()[ASSIGNMENTS_COLLECTION].update_one(
                {"_id": ObjectId(assignment_id)},
                {"$set": {
                    "finished_at": datetime.datetime.utcnow(),
                    "score": int(body.get("correct", 0)),
                    "total_with_keys": int(body.get("total_with_keys", 0)),
                    "attempted": int(body.get("attempted", 0)),
                }}
            )
    except Exception:
        pass
    return jsonify({"ok": True})


@scores_bp.route("/api/scores", methods=["GET"])  # admin lists scores
def list_scores():
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    cursor = get_db()[SCORES_COLLECTION].find({}, {"_id": 0}).sort("created_at", -1)
    return jsonify(list(cursor))


