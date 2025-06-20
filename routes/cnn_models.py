import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from flask import Blueprint, jsonify, request

# Define the Flask blueprint
cnn_models_bp = Blueprint("cnn_models", __name__)

@cnn_models_bp.route("/cnn-models", methods=["GET"])
def get_cnn_models():
    """
    Example route for CNN models.
    """
    return jsonify({"message": "This is the CNN models endpoint."})

@cnn_models_bp.route("/cnn-models/predict", methods=["POST"])
def predict():
    """
    Predict using the CNN model.
    """
    try:
        # Load the model (ensure the model is trained and saved beforehand)
        model = CNNModel()
        model.load_state_dict(torch.load("cnn_model.pth"))  # Use the correct relative path
        model.eval()

        # Parse input data
        input_data = request.json.get("data")
        if input_data is None:
            return jsonify({"error": "No input data provided"}), 400

        # Convert input data to tensor
        input_tensor = torch.tensor(input_data, dtype=torch.float32).unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions

        # Make prediction
        with torch.no_grad():
            output = model(input_tensor)
            prediction = torch.argmax(output, dim=1).item()

        return jsonify({"prediction": prediction})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper function to calculate flattened size
def calculate_flattened_size(model, input_shape):
    with torch.no_grad():
        x = torch.zeros(input_shape)
        x = model.pool(F.relu(model.conv1(x)))
        x = model.pool(F.relu(model.conv2(x)))
        return x.numel()

# Define the CNN model
class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

        # Dynamically calculate the flattened size
        flattened_size = calculate_flattened_size(self, (1, 1, 100))
        self.fc1 = nn.Linear(flattened_size, 128)
        self.fc2 = nn.Linear(128, 2)  # Output: 2 classes (e.g., planet or no planet)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)  # Flatten the tensor
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Initialize model, loss function, and optimizer
model = CNNModel()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Dummy training loop
for epoch in range(10):
    inputs = torch.randn(32, 1, 100)  # Batch size = 32, Channels = 1, Sequence length = 100
    labels = torch.randint(0, 2, (32,))  # Batch size = 32

    optimizer.zero_grad()
    outputs = model(inputs)
    print(f"Model output shape: {outputs.shape}")  # Debugging
    print(f"Labels shape: {labels.shape}")  # Debugging
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch+1}, Loss: {loss.item()}")

# Save the trained model
torch.save(model.state_dict(), "cnn_model.pth")