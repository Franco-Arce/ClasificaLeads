import json
from logic import process_data

# Load test data
with open('test_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data.get('items', []))} messages")

# Process
results = process_data(data)

print(f"\nProcessed {len(results)} conversations\n")

# Summary
spam_count = sum(1 for r in results if r['clasificacion'] == 'SPAM')
mql_count = sum(1 for r in results if r['clasificacion'] == 'MQL')
sql_count = sum(1 for r in results if r['clasificacion'] == 'SQL')

print(f"SPAM: {spam_count}")
print(f"MQL: {mql_count}")
print(f"SQL: {sql_count}")

print("\n--- Sample Results ---")
for r in results[:5]:
    print(f"\nChat: {r['chat_id'][:20]}...")
    print(f"  Clasificacion: {r['clasificacion']}")
    print(f"  Score Total: {r['score_total']}")
    print(f"  - Motivacion: {r['score_motivacion']}")
    print(f"  - Pago: {r['score_pago']}")
    print(f"  - Comportamiento: {r['score_comportamiento']}")
    print(f"  Razon: {r['razon_principal']}")
    signals = r['señales_clave'][:3] if len(r['señales_clave']) > 3 else r['señales_clave']
    print(f"  Senales: {signals}")
