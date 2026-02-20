


import json
import pandas as pd
import os
import sys
import importlib.util

# Define paths
base_path = r"c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\AnalizarClasificacion"
json_1 = os.path.join(base_path, "bulk_export_nodslabsas-whatsapp-593998348706_2026-02-12.json")
json_2 = os.path.join(base_path, "bulk_export_nodslabsas-whatsapp-593998348706_2026-02-12 (1).json")

# Force load logic from ClasificaLeadsMkt
logic_path = r"c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\ClasificaLeadsMkt\logic.py"
spec = importlib.util.spec_from_file_location("logic_mkt", logic_path)
logic_mkt = importlib.util.module_from_spec(spec)
sys.modules["logic_mkt"] = logic_mkt
spec.loader.exec_module(logic_mkt)
process_data = logic_mkt.process_data

target_phones = ["593997090163", "593958752306", "593968409232"]

def extract_chat_info(json_path, targets):
    output_file = "analysis_with_scoring.txt"
    
    with open(output_file, "a", encoding="utf-8") as f:
        print(f"--- Processing {os.path.basename(json_path)} with NEW SCORING LOGIC ---", file=f)
        
        # 1. Load JSON Input
        try:
            with open(json_path, 'r', encoding='utf-8') as json_f:
                data = json.load(json_f)
        except Exception as e:
            print(f"Error reading JSON {json_path}: {e}", file=f)
            return

        # 2. Run Process Data with New Logic
        # We don't need neotel_df for the core scoring analysis, passing None for now to isolate logic
        print("Running process_data...", file=f)
        results = process_data(data, neotel_df=None)
        
        # 3. Process targets
        for phone in targets:
            # Find result for this phone
            # Logic now returns 'telefono' in result
            
            # Filter results for this phone
            # We match by string containment just in case of format diffs
            target_res = [r for r in results if str(phone) in str(r.get('telefono', ''))]
            
            if not target_res:
                # Try finding it in the source items to confirm it exists but maybe wasn't processed?
                items = data.get('items', [])
                user_msgs = [i for i in items if i.get('chat', {}).get('contactId') == phone]
                if user_msgs:
                     print(f"\nFOUND PHONE IN JSON: {phone}, BUT NO RESULT PRODUCED!", file=f)
                continue
                
            print(f"\nFOUND PHONE RESULT: {phone}", file=f)
            
            for res in target_res:
                print("CLASSIFICATION RESULT (Computed Now):", file=f)
                print(f"  Clasificacion: {res.get('clasificacion')}", file=f)
                print(f"  Razon: {res.get('razon_principal')}", file=f)
                print(f"  Score Total: {res.get('score_total')}", file=f)
                print(f"  Score Motivacion: {res.get('score_motivacion')}", file=f)
                print(f"  Score Pago: {res.get('score_pago')}", file=f)
                print(f"  Score Comportamiento: {res.get('score_comportamiento')}", file=f)
                print(f"  Señales: {res.get('señales_clave')}", file=f)
                print(f"  Estado: {res.get('estado_conversacion')}", file=f)


# Clear file on run
with open("analysis_with_scoring.txt", "w", encoding="utf-8") as f:
    f.write("")


# Extract all 3 target phones
extract_chat_info(json_1, target_phones)
extract_chat_info(json_2, target_phones)
