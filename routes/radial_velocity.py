from flask import Blueprint, request, jsonify
import torch
from .cnn_models import CNNModel  # Corrected import path

radial_velocity_bp = Blueprint('radial_velocity', __name__)

# Load the trained model
model = CNNModel()
model.load_state_dict(torch.load("cnn_model.pth"))  # Use the correct relative path
model.eval()

@radial_velocity_bp.route('/api/predict', methods=['POST'])
def predict():
    """
    API endpoint to predict exoplanet detection from radial velocity data.
    """
    try:
        data = request.json.get("radial_velocity")  # Expecting a list of radial velocity data
        if not data:
            return jsonify({"error": "No radial velocity data provided"}), 400

        # Preprocess the data
        input_data = torch.tensor([data], dtype=torch.float32).unsqueeze(0)  # Add batch and channel dimensions

        # Make prediction
        with torch.no_grad():
            output = model(input_data)
            prediction = torch.argmax(output, dim=1).item()

        return jsonify({"prediction": "planet" if prediction == 1 else "no planet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500