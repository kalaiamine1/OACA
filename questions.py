import os
import json
import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify
from bson import ObjectId

from configuration import get_db, QUESTIONS_COLLECTION, SECTIONS_COLLECTION, USER_ATTEMPTS_COLLECTION
from login import _current_user_claims

questions_bp = Blueprint('questions', __name__)

# --- Question Management API ---

@questions_bp.route("/api/questions", methods=["GET"])
def get_questions():
    """Get all questions with optional filtering by section"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Only admins can manage questions
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    section_filter = request.args.get("section")
    db = get_db()
    
    query = {}
    if section_filter:
        query["section"] = section_filter
    
    questions = list(db[QUESTIONS_COLLECTION].find(query).sort("section", 1).sort("id", 1))
    
    # Convert ObjectId to string for JSON serialization
    for question in questions:
        question["_id"] = str(question["_id"])
    
    return jsonify(questions)

@questions_bp.route("/api/questions", methods=["POST"])
def create_question():
    """Create a new question"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    body = request.get_json(silent=True) or {}
    
    required_fields = ["question", "answers", "correct_answer", "section"]
    for field in required_fields:
        if field not in body:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate answers format
    answers = body.get("answers", [])
    if not isinstance(answers, list) or len(answers) < 2:
        return jsonify({"error": "At least 2 answers required"}), 400
    
    # Validate correct_answer
    correct_answer = body.get("correct_answer")
    if correct_answer not in ["A", "B", "C", "D"]:
        return jsonify({"error": "correct_answer must be A, B, C, or D"}), 400
    
    # Get next question ID for the section
    db = get_db()
    section = body.get("section")
    last_question = db[QUESTIONS_COLLECTION].find_one(
        {"section": section}, 
        sort=[("id", -1)]
    )
    next_id = (last_question.get("id", 0) + 1) if last_question else 1
    
    # Convert answers array to options dict
    options = {}
    for i, answer in enumerate(answers):
        options[chr(65 + i)] = answer  # A, B, C, D
    
    question_doc = {
        "id": next_id,
        "question": body.get("question"),
        "answers": answers,
        "options": options,
        "correct_answer": correct_answer,
        "section": section,
        "created_at": datetime.datetime.utcnow(),
        "created_by": claims.get("email")
    }
    
    result = db[QUESTIONS_COLLECTION].insert_one(question_doc)
    question_doc["_id"] = str(result.inserted_id)
    
    return jsonify(question_doc), 201

@questions_bp.route("/api/questions/<question_id>", methods=["PUT"])
def update_question(question_id):
    """Update an existing question"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    body = request.get_json(silent=True) or {}
    
    # Validate answers format if provided
    if "answers" in body:
        answers = body.get("answers", [])
        if not isinstance(answers, list) or len(answers) < 2:
            return jsonify({"error": "At least 2 answers required"}), 400
        
        # Convert answers array to options dict
        options = {}
        for i, answer in enumerate(answers):
            options[chr(65 + i)] = answer  # A, B, C, D
        body["options"] = options
    
    # Validate correct_answer if provided
    if "correct_answer" in body:
        correct_answer = body.get("correct_answer")
        if correct_answer not in ["A", "B", "C", "D"]:
            return jsonify({"error": "correct_answer must be A, B, C, or D"}), 400
    
    db = get_db()
    body["updated_at"] = datetime.datetime.utcnow()
    body["updated_by"] = claims.get("email")
    
    result = db[QUESTIONS_COLLECTION].update_one(
        {"_id": ObjectId(question_id)},
        {"$set": body}
    )
    
    if result.matched_count == 0:
        return jsonify({"error": "Question not found"}), 404
    
    return jsonify({"message": "Question updated successfully"})

@questions_bp.route("/api/questions/<question_id>", methods=["DELETE"])
def delete_question(question_id):
    """Delete a question"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    result = db[QUESTIONS_COLLECTION].delete_one({"_id": ObjectId(question_id)})
    
    if result.deleted_count == 0:
        return jsonify({"error": "Question not found"}), 404
    
    return jsonify({"message": "Question deleted successfully"})

# --- Section Management API ---

@questions_bp.route("/api/sections", methods=["GET"])
def get_sections():
    """Get all sections"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    sections = list(db[SECTIONS_COLLECTION].find().sort("name", 1))
    
    # Add question count for each section
    for section in sections:
        section["_id"] = str(section["_id"])
        question_count = db[QUESTIONS_COLLECTION].count_documents({"section": section["name"]})
        section["question_count"] = question_count
    
    return jsonify(sections)

@questions_bp.route("/api/sections", methods=["POST"])
def create_section():
    """Create a new section"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    body = request.get_json(silent=True) or {}
    
    if "name" not in body:
        return jsonify({"error": "Section name is required"}), 400
    
    db = get_db()
    
    # Check if section already exists
    existing = db[SECTIONS_COLLECTION].find_one({"name": body["name"]})
    if existing:
        return jsonify({"error": "Section already exists"}), 400
    
    section_doc = {
        "name": body["name"],
        "description": body.get("description", ""),
        "created_at": datetime.datetime.utcnow(),
        "created_by": claims.get("email")
    }
    
    result = db[SECTIONS_COLLECTION].insert_one(section_doc)
    section_doc["_id"] = str(result.inserted_id)
    section_doc["question_count"] = 0
    
    return jsonify(section_doc), 201

@questions_bp.route("/api/sections/<section_id>", methods=["PUT"])
def update_section(section_id):
    """Update an existing section"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    body = request.get_json(silent=True) or {}
    
    db = get_db()
    body["updated_at"] = datetime.datetime.utcnow()
    body["updated_by"] = claims.get("email")
    
    result = db[SECTIONS_COLLECTION].update_one(
        {"_id": ObjectId(section_id)},
        {"$set": body}
    )
    
    if result.matched_count == 0:
        return jsonify({"error": "Section not found"}), 404
    
    return jsonify({"message": "Section updated successfully"})

@questions_bp.route("/api/sections/<section_id>", methods=["DELETE"])
def delete_section(section_id):
    """Delete a section and all its questions"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    
    # Get section name before deleting
    section = db[SECTIONS_COLLECTION].find_one({"_id": ObjectId(section_id)})
    if not section:
        return jsonify({"error": "Section not found"}), 404
    
    section_name = section["name"]
    
    # Delete all questions in this section
    db[QUESTIONS_COLLECTION].delete_many({"section": section_name})
    
    # Delete the section
    result = db[SECTIONS_COLLECTION].delete_one({"_id": ObjectId(section_id)})
    
    return jsonify({"message": f"Section '{section_name}' and all its questions deleted successfully"})

# --- User Attempt Tracking API ---

@questions_bp.route("/api/user-attempts/<user_email>", methods=["GET"])
def get_user_attempts(user_email):
    """Get user's attempt count and status"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Users can only check their own attempts, admins can check anyone
    if claims.get("role") != "admin" and claims.get("email") != user_email:
        return jsonify({"error": "Forbidden"}), 403
    
    db = get_db()
    attempt_record = db[USER_ATTEMPTS_COLLECTION].find_one({"email": user_email})
    
    if not attempt_record:
        return jsonify({
            "email": user_email,
            "attempts_used": 0,
            "max_attempts": 3,
            "remaining_attempts": 3,
            "can_attempt": True,
            "last_attempt": None
        })
    
    attempts_used = attempt_record.get("attempts_used", 0)
    max_attempts = 3
    remaining = max(0, max_attempts - attempts_used)
    
    return jsonify({
        "email": user_email,
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "remaining_attempts": remaining,
        "can_attempt": remaining > 0,
        "last_attempt": attempt_record.get("last_attempt")
    })

@questions_bp.route("/api/user-attempts/<user_email>", methods=["POST"])
def record_attempt(user_email):
    """Record a new attempt for a user"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Users can only record their own attempts, admins can record for anyone
    if claims.get("role") != "admin" and claims.get("email") != user_email:
        return jsonify({"error": "Forbidden"}), 403
    
    db = get_db()
    
    # Check current attempt count
    attempt_record = db[USER_ATTEMPTS_COLLECTION].find_one({"email": user_email})
    attempts_used = attempt_record.get("attempts_used", 0) if attempt_record else 0
    
    if attempts_used >= 3:
        return jsonify({"error": "Maximum attempts (3) already used"}), 400
    
    # Increment attempt count
    new_count = attempts_used + 1
    now = datetime.datetime.utcnow()
    
    db[USER_ATTEMPTS_COLLECTION].update_one(
        {"email": user_email},
        {
            "$set": {
                "email": user_email,
                "attempts_used": new_count,
                "last_attempt": now,
                "updated_at": now
            }
        },
        upsert=True
    )
    
    remaining = 3 - new_count
    
    return jsonify({
        "email": user_email,
        "attempts_used": new_count,
        "max_attempts": 3,
        "remaining_attempts": remaining,
        "can_attempt": remaining > 0,
        "last_attempt": now.isoformat()
    })

# --- Migration API ---

@questions_bp.route("/api/migrate-questions", methods=["POST"])
def migrate_questions():
    """Migrate questions from JSON file to database"""
    claims = _current_user_claims()
    if not claims:
        return jsonify({"error": "Unauthorized"}), 401
    
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        # Load questions from JSON file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "aviation_quiz_data.json")
        
        with open(data_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        
        db = get_db()
        migrated_sections = 0
        migrated_questions = 0
        
        # Process exams and activities
        if "exams" in data:
            for exam in data.get("exams", []):
                for activity in exam.get("activities", []):
                    section_name = activity.get("title", "Unknown")
                    
                    # Create section if it doesn't exist
                    existing_section = db[SECTIONS_COLLECTION].find_one({"name": section_name})
                    if not existing_section:
                        section_doc = {
                            "name": section_name,
                            "description": f"Migrated from {exam.get('title', 'Unknown Exam')}",
                            "created_at": datetime.datetime.utcnow(),
                            "created_by": claims.get("email")
                        }
                        db[SECTIONS_COLLECTION].insert_one(section_doc)
                        migrated_sections += 1
                    
                    # Process questions
                    for q in activity.get("questions", []):
                        if q.get("id") is not None:
                            # Convert answers array to options dict
                            answers = q.get("answers", [])
                            options = {}
                            for i, answer in enumerate(answers):
                                options[chr(65 + i)] = answer  # A, B, C, D
                            
                            question_doc = {
                                "id": q.get("id"),
                                "question": q.get("question"),
                                "answers": answers,
                                "options": options,
                                "correct_answer": q.get("correct_answer", "A"),  # Default to first answer
                                "section": section_name,
                                "created_at": datetime.datetime.utcnow(),
                                "created_by": claims.get("email")
                            }
                            
                            # Check if question already exists
                            existing = db[QUESTIONS_COLLECTION].find_one({
                                "section": section_name,
                                "id": q.get("id")
                            })
                            
                            if not existing:
                                db[QUESTIONS_COLLECTION].insert_one(question_doc)
                                migrated_questions += 1
        
        return jsonify({
            "message": "Migration completed successfully",
            "sections_created": migrated_sections,
            "questions_migrated": migrated_questions
        })
        
    except Exception as e:
        return jsonify({"error": f"Migration failed: {str(e)}"}), 500
