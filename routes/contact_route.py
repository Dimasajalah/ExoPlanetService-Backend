from flask import Blueprint, request, jsonify
from datetime import datetime
from extensions import mongo

contact_bp = Blueprint("contact", __name__)

@contact_bp.route("/api/contact", methods=["POST"])
def handle_contact():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        contact_doc = {
            "name": name,
            "email": email,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        mongo.db.contacts.insert_one(contact_doc)
        return jsonify({"message": "Message received"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@contact_bp.route("/api/contact-messages", methods=["GET"])
def get_contact_messages():
    try:
        messages = list(mongo.db.contacts.find({}, {"_id": 0}))
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
   
