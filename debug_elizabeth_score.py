import sys
import os
import json
import pandas as pd

import importlib.util

# Load logic.py specifically from ClasificaLeadsMkt
spec = importlib.util.spec_from_file_location("logic", r'c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\ClasificaLeadsMkt\logic.py')
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)
analyze_conversation = logic.analyze_conversation

def debug_chat():
    json_path = r'c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\AnalizarClasificacion\bulk_export_nodslabsas-whatsapp-593998348706_2026-02-18.json'
    target_contact_id = "593982438196"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    items = data.get('items', [])
    chat_messages = [m for m in items if m.get('chat', {}).get('contactId') == target_contact_id]
    
    if not chat_messages:
        print(f"No messages found for contact {target_contact_id}")
        return
        
    # analyze_conversation expects (chat_id, messages)
    chat_id = chat_messages[0].get('chat', {}).get('chatId')
    
    # Let's see what keywords match manually to debug
    motivation_keywords = [
        "trabajo", "ascenso", "profesional", "laboral", "cv", "curriculum", "mejorar", 
        "crecimiento", "personal", "aprender", "actualizado", "requerimiento",
        "empleo", "puesto", "cargo", "superación", "conocimiento", "carrera", "estudio"
    ]
    
    print("--- Debugging Keywords ---")
    for msg in chat_messages:
        if msg.get('from') == 'user':
            text = msg.get('content', {}).get('text', '').lower()
            for kw in motivation_keywords:
                if kw in text:
                    print(f"Match found: '{kw}' in message: '{text}'")

    result = analyze_conversation(chat_id, chat_messages)
    print("--- Analysis Result ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    debug_chat()
