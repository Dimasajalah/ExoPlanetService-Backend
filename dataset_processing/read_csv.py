import pandas as pd

# Ganti 'TD_2025.05.04_02.36.16.csv' dengan path file CSV Anda
file_path = 'TD_2025.05.04_02.36.16.csv'

try:
    # Membaca file CSV dengan penanganan error
    data = pd.read_csv(file_path, on_bad_lines='skip', encoding='utf-8')  # Abaikan baris yang bermasalah
    print("Nama Kolom:")
    print(data.columns.tolist())  # Menampilkan nama kolom
    print("\nContoh Data:")
    print(data.head())  # Menampilkan 5 baris pertama
except Exception as e:
    print(f"Error membaca file CSV: {e}")