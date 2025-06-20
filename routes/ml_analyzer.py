# routes/ml_analyzer.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.cnn_model import predict_dummy
from services.db import mongo
from datetime import datetime
import pandas as pd
import os

ml_analyzer_bp = Blueprint("ml_analyzer", __name__)

@ml_analyzer_bp.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)

    try:
        df = pd.read_csv(file)
        result = predict_dummy(df)

        # Simpan ke MongoDB
        mongo.db.cnn_predictions.insert_one({
            "filename": filename,
            "planet_detected": result["planet_detected"],
            "confidence": result["confidence"],
            "timestamp": datetime.utcnow()
        })

        return jsonify({
            "filename": filename,
            "prediction": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
