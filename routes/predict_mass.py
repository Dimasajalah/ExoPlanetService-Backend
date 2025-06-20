from flask import Blueprint, request, jsonify
import joblib
import os
import numpy as np
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Inisialisasi Blueprint
predict_mass_bp = Blueprint('predict_mass', __name__)

# Lokasi folder model
model_folder = "backend"

@predict_mass_bp.route('/api/predict_mass', methods=['POST'])
def predict_mass():
    """
    Endpoint untuk memprediksi massa planet berdasarkan fitur input dan dataset yang dipilih.

    Input (JSON):
    {
        "dataset": str,      # Nama dataset (misalnya, "Dataset1")
        "pl_orbper": float,  # Periode orbit (dalam hari)
        "pl_rade": float,    # Radius planet (dalam radius Bumi)
        "st_teff": float,    # Temperatur bintang (dalam Kelvin)
        "model": "random_forest" or "xgboost"  # Pilihan model
    }

    Output (JSON):
    {
        "predicted_mass": float  # Massa planet yang diprediksi (dalam massa Bumi)
    }
    """
    try:
        # Ambil data input dari request JSON
        data = request.json

        # Validasi input
        if not all(key in data for key in ['dataset', 'pl_orbper', 'pl_rade', 'st_teff', 'model']):
            return jsonify({"error": "Missing required fields: 'dataset', 'pl_orbper', 'pl_rade', 'st_teff', 'model'"}), 400

        dataset_name = data['dataset']
        model_type = data['model']

        # Validasi apakah dataset tersedia
        scaler_path = os.path.join(model_folder, f"{dataset_name}_scaler.pkl")
        rf_model_path = os.path.join(model_folder, f"{dataset_name}_random_forest_model.pkl")
        xgb_model_path = os.path.join(model_folder, f"{dataset_name}_xgboost_model.pkl")

        if not os.path.exists(scaler_path) or not os.path.exists(rf_model_path) or not os.path.exists(xgb_model_path):
            return jsonify({"error": f"Models for dataset '{dataset_name}' not found."}), 404

        # Load scaler dan model
        scaler = joblib.load(scaler_path)
        if model_type == "random_forest":
            model = joblib.load(rf_model_path)
        elif model_type == "xgboost":
            model = joblib.load(xgb_model_path)
        else:
            return jsonify({"error": "Invalid model type. Choose 'random_forest' or 'xgboost'"}), 400

        # Ambil fitur dari input
        features = np.array([data['pl_orbper'], data['pl_rade'], data['st_teff']]).reshape(1, -1)

        # Normalisasi fitur
        features_scaled = scaler.transform(features)

        # Prediksi massa planet
        prediction = model.predict(features_scaled)

        return jsonify({"predicted_mass": prediction[0]})
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return jsonify({"error": "An error occurred during prediction", "details": str(e)}), 500
    
@predict_mass_bp.route('/api/datasets', methods=['GET'])
def list_datasets():
    """
    Endpoint untuk mengembalikan daftar dataset yang tersedia.
    """
    folder = "backend/dataset_processing"
    datasets = [os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith(".csv")]
    return jsonify(datasets)