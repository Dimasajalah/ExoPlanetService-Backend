import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from xgboost import XGBRegressor

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Lokasi folder dataset
dataset_folder = os.path.dirname(__file__)

# Dapatkan semua file CSV di folder dataset
datasets = [f for f in os.listdir(dataset_folder) if f.endswith(".csv")]

# Validasi apakah ada dataset
if not datasets:
    logging.error("Tidak ada file CSV di folder dataset_processing.")
    raise ValueError("Folder dataset_processing kosong. Tidak dapat melanjutkan.")

# File log untuk dataset yang dilewati
skipped_log_file = os.path.join(dataset_folder, "skipped_datasets.log")
with open(skipped_log_file, "w") as log_file:
    log_file.write("Dataset yang dilewati:\n")

# Proses setiap dataset
for dataset in datasets:
    logging.info(f"Memproses dataset: {dataset}")
    csv_file = os.path.join(dataset_folder, dataset)

    # Membaca data dari file CSV dengan penanganan error
    try:
        logging.info(f"Membaca data dari file {dataset}...")
        # Melewati baris metadata dan menentukan delimiter
        data = pd.read_csv(csv_file, skiprows=1, delimiter=',', on_bad_lines='skip', encoding='utf-8')
    except Exception as e:
        logging.error(f"Error membaca file {dataset}: {e}")
        with open(skipped_log_file, "a") as log_file:
            log_file.write(f"{dataset}: Error membaca file - {e}\n")
        continue

    # Debugging: Tampilkan nama kolom
    logging.info(f"Kolom yang tersedia di {dataset}: {list(data.columns)}")

    # Mapping nama kolom jika berbeda
    column_mapping = {
        'orbital_period': 'pl_orbper',
        'planet_radius': 'pl_rade',
        'stellar_temperature': 'st_teff',
        'planet_mass': 'pl_bmasse'
    }
    data.rename(columns=column_mapping, inplace=True)

    # Validasi data
    if data.empty:
        logging.warning(f"Dataset {dataset} kosong. Melewati dataset ini.")
        with open(skipped_log_file, "a") as log_file:
            log_file.write(f"{dataset}: Dataset kosong\n")
        continue

    # Cek apakah kolom yang diperlukan ada
    required_columns = ['pl_orbper', 'pl_rade', 'st_teff', 'pl_bmasse']
    if not all(col in data.columns for col in required_columns):
        logging.warning(f"Dataset {dataset} tidak memiliki kolom yang diperlukan setelah mapping: {required_columns}. Melewati dataset ini.")
        with open(skipped_log_file, "a") as log_file:
            log_file.write(f"{dataset}: Kolom tidak lengkap - {list(data.columns)}\n")
        continue

    # Debugging: Tampilkan beberapa baris pertama dari dataset
    logging.info(f"Contoh data dari {dataset}:\n{data.head()}")

    # Hapus baris dengan nilai yang hilang (NaN)
    logging.info(f"Menghapus baris dengan nilai NaN dari {dataset}...")
    data = data.dropna()

    # Pilih fitur dan label
    X = data[['pl_orbper', 'pl_rade', 'st_teff']]  # Fitur
    y = data['pl_bmasse']  # Label

    # Normalisasi fitur
    logging.info(f"Normalisasi fitur untuk {dataset}...")
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Bagi data menjadi training dan testing
    logging.info(f"Membagi data menjadi training dan testing untuk {dataset}...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Inisialisasi model Random Forest
    logging.info(f"Inisialisasi model Random Forest untuk {dataset}...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Latih model Random Forest
    logging.info(f"Melatih model Random Forest untuk {dataset}...")
    rf_model.fit(X_train, y_train)

    # Prediksi pada data testing dengan Random Forest
    logging.info(f"Melakukan prediksi pada data testing dengan Random Forest untuk {dataset}...")
    y_pred_rf = rf_model.predict(X_test)

    # Evaluasi model Random Forest
    logging.info(f"Evaluasi model Random Forest untuk {dataset}...")
    mse_rf = mean_squared_error(y_test, y_pred_rf)
    logging.info(f"Mean Squared Error (Random Forest) untuk {dataset}: {mse_rf}")

    # Inisialisasi model Gradient Boosting (XGBoost)
    logging.info(f"Inisialisasi model Gradient Boosting (XGBoost) untuk {dataset}...")
    xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)

    # Latih model Gradient Boosting
    logging.info(f"Melatih model Gradient Boosting (XGBoost) untuk {dataset}...")
    xgb_model.fit(X_train, y_train)

    # Prediksi pada data testing dengan Gradient Boosting
    logging.info(f"Melakukan prediksi pada data testing dengan Gradient Boosting untuk {dataset}...")
    y_pred_xgb = xgb_model.predict(X_test)

    # Evaluasi model Gradient Boosting
    logging.info(f"Evaluasi model Gradient Boosting untuk {dataset}...")
    mse_xgb = mean_squared_error(y_test, y_pred_xgb)
    logging.info(f"Mean Squared Error (XGBoost) untuk {dataset}: {mse_xgb}")

    # Simpan scaler dan model ke file
    logging.info(f"Menyimpan scaler dan model untuk {dataset} ke file...")
    dataset_name = os.path.splitext(dataset)[0]
    joblib.dump(scaler, f"backend/{dataset_name}_scaler.pkl")
    joblib.dump(rf_model, f"backend/{dataset_name}_random_forest_model.pkl")
    joblib.dump(xgb_model, f"backend/{dataset_name}_xgboost_model.pkl")
    logging.info(f"Scaler dan model untuk {dataset} berhasil disimpan.")

logging.info("Proses semua dataset selesai.")
