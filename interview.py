from flask import Blueprint, request, jsonify
from configuration import get_meetings_collection
from datetime import datetime

# Créer un blueprint pour les entretiens
interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/planifier', methods=['POST'])
def planifier_entretien():
    """
    Endpoint pour planifier un entretien.
    Expects JSON: { email, datetime, duration, zoom_link }
    """
    data = request.get_json()

    email = data.get('email')
    datetime_str = data.get('datetime')
    duration = data.get('duration')
    zoom_link = data.get('zoom_link')

    if not email or not datetime_str or not duration or not zoom_link:
        return jsonify({"success": False, "error": "Tous les champs sont requis."}), 400

    try:
        # Convertir datetime en objet Python
        interview_datetime = datetime.fromisoformat(datetime_str)
        if interview_datetime <= datetime.utcnow():
            return jsonify({"success": False, "error": "La date doit être dans le futur."}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Format de date invalide."}), 400

    meeting = {
        "email": email,
        "datetime": interview_datetime,
        "duration": int(duration),
        "zoom_link": zoom_link
    }

    try:
        meetings_col = get_meetings_collection()
        meetings_col.insert_one(meeting)
        return jsonify({"success": True, "zoom_link": zoom_link})
    except Exception as e:
        return jsonify({"success": False, "error": "Erreur serveur: " + str(e)}), 500

@interview_bp.route('/meetings', methods=['GET'])
def get_meetings():
    """
    Retourne toutes les réunions planifiées.
    """
    try:
        meetings_col = get_meetings_collection()
        meetings = list(meetings_col.find({}, {"_id":0}).sort("datetime", 1))
        # Convertir datetime en isoformat pour JSON
        for m in meetings:
            m["datetime"] = m["datetime"].isoformat()
        return jsonify(meetings)
    except Exception as e:
        return jsonify([]), 500
