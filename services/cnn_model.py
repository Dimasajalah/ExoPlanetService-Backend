# services/cnn_model.py
import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import StandardScaler

# Fitur yang digunakan dari dataset Anda (pastikan kolom ini ada di CSV)
SELECTED_FEATURES = [
    "pl_orbper", "pl_rade", "pl_masse", "pl_dens",
    "pl_eqt", "st_teff", "st_mass", "st_rad"
]

# Dummy CNN model
class DummyCNN(nn.Module):
    def __init__(self, input_size):
        super(DummyCNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),  # output: [planet_detected (bool), confidence]
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)

# Load model dummy
model = DummyCNN(input_size=len(SELECTED_FEATURES))
model.eval()

# Dummy preprocess: extract fitur, isi NaN, normalisasi, ke tensor
def preprocess(df):
    df = df[SELECTED_FEATURES].copy()
    df.fillna(-1, inplace=True)  # Isi NaN dengan -1

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df.values)
    tensor = torch.tensor(X_scaled, dtype=torch.float32)

    return tensor

# Dummy prediksi CNN (ambil 1 baris pertama)
def predict_dummy(df):
    tensor = preprocess(df)
    if tensor.shape[0] == 0:
        return {
            "planet_detected": False,
            "confidence": 0.0
        }
    output = model(tensor[0].unsqueeze(0)).detach().numpy()[0]
    return {
        "planet_detected": output[0] > 0.5,
        "confidence": float(output[1])
    }
