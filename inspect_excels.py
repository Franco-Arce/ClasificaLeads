
import pandas as pd
import os

base_path = r"c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\AnalizarClasificacion"
excel_1 = os.path.join(base_path, "leads_clasificados.xlsx")
excel_2 = os.path.join(base_path, "leads_clasificados(1).xlsx")

def inspect_excel(path, name):
    print(f"\n--- Inspecting {name} ---")
    try:
        df = pd.read_excel(path)
        print(f"Columns: {list(df.columns)}")
        if 'telefono' in df.columns:
            print("First 10 phones:")
            print(df['telefono'].head(10))
            print("Data types:")
            print(df['telefono'].dtype)
            
            # Check if our missing phones are in there in any format
            targets = ["593958752306", "593968409232"]
            for t in targets:
                # Check string contains
                matches = df[df['telefono'].astype(str).str.contains(t, na=False)]
                if not matches.empty:
                    print(f"FOUND {t} in {name} (row {matches.index[0]})")
                else:
                    # Check if it's there without country code?
                    short_t = t[3:] # Remove 593
                    matches_short = df[df['telefono'].astype(str).str.contains(short_t, na=False)]
                    if not matches_short.empty:
                        print(f"FOUND {t} as {matches_short.iloc[0]['telefono']} in {name} (short match)")
                    else:
                        print(f"NOT FOUND {t} in {name}")
        else:
            print("No 'telefono' column found!")
    except Exception as e:
        print(f"Error reading {name}: {e}")

output_file = "excel_inspection.txt"
# Redirect stdout to file
import sys
original_stdout = sys.stdout
with open(output_file, "w", encoding="utf-8") as f:
    sys.stdout = f
    inspect_excel(excel_1, "leads_clasificados.xlsx")
    inspect_excel(excel_2, "leads_clasificados(1).xlsx")
    sys.stdout = original_stdout

print(f"Inspection written to {output_file}")
