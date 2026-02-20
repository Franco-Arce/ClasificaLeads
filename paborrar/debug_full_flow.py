"""
Debug script to test the full flow from JSON to final output with UTM data
"""
import json
import pandas as pd
from logic import process_data

# 1. Load Neotel data
print("="*60)
print("LOADING NEOTEL DATA")
print("="*60)
neotel_df = pd.read_excel('NotraeUTm/DatabaseQuery_34_30122025_10135276.xls')
print(f"Total records: {len(neotel_df)}")
print(f"\nColumns: {list(neotel_df.columns)}")
print(f"\nSample UTM Medium values:")
print(neotel_df['UTM Medium'].value_counts().head(10))

# 2. Create a minimal test JSON that simulates a chat
test_phone = "593993575726"  # Phone with 'cpc' UTM Medium
test_json = {
    "items": [
        {
            "chat": {
                "chatId": "TEST_CHAT_001",
                "contactId": test_phone
            },
            "from": "user",
            "content": {
                "type": "text",
                "text": "hola quiero mas informacion sobre el programa"
            },
            "creationTime": "2024-01-15T10:00:00Z"
        },
        {
            "chat": {
                "chatId": "TEST_CHAT_001",
                "contactId": test_phone
            },
            "from": "user",
            "content": {
                "type": "text",
                "text": "me interesa para mejorar mi perfil profesional"
            },
            "creationTime": "2024-01-15T10:05:00Z"
        },
        {
            "chat": {
                "chatId": "TEST_CHAT_001",
                "contactId": test_phone
            },
            "from": "bot",
            "content": {
                "type": "text",
                "text": "perfecto, te enviamos la informacion"
            },
            "creationTime": "2024-01-15T10:06:00Z"
        }
    ]
}

# 3. Process the data
print("\n" + "="*60)
print("PROCESSING DATA")
print("="*60)
results = process_data(test_json, neotel_df)

# 4. Display results
print(f"\nProcessed {len(results)} conversations")
for result in results:
    print("\n" + "-"*60)
    print(f"Chat ID: {result.get('chat_id')}")
    print(f"Telefono: {result.get('telefono')}")
    print(f"Clasificacion: {result.get('clasificacion')}")
    print(f"Razon: {result.get('razon_principal')}")
    print(f"\n[UTM DATA]")
    print(f"  utm_source: {result.get('utm_source')}")
    print(f"  utm_medium: {result.get('utm_medium')}")
    print(f"  utm_origen: {result.get('utm_origen')}")
    print(f"  programa_interes: {result.get('programa_interes')}")
    print(f"\nSignals: {result.get('señales_clave')}")
    
# 5. Verify
print("\n" + "="*60)
if result.get('utm_medium'):
    print("[SUCCESS] UTM Medium was extracted in the full flow!")
else:
    print("[FAILED] UTM Medium is still empty in the full flow")
print("="*60)
