import pandas as pd
import os

file_path = r"C:\Users\franc\OneDrive\Escritorio\Mis Cosas\ClasificaLeads\NotraeUTm\DatabaseQuery_34_30122025_10135276.xls"

try:
    df = pd.read_excel(file_path)
    print("Columns found in Excel file:")
    for col in df.columns:
        print(f"'{col}'")
except Exception as e:
    print(f"Error reading file: {e}")
