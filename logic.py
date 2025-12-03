import json
from datetime import datetime
from collections import defaultdict

def group_and_sort(items):
    """
    Groups items by chatId and sorts them by creationTime.
    """
    grouped = defaultdict(list)
    for item in items:
        # Extract chatId safely
        chat_id = item.get('chat', {}).get('chatId')
        if chat_id:
            grouped[chat_id].append(item)
    
    # Sort each group by creationTime
    for chat_id in grouped:
        grouped[chat_id].sort(key=lambda x: x.get('creationTime', ''))
        
    return grouped

def analyze_conversation(chat_id, messages):
    """
    Analyzes a single conversation to determine if it's SQL or MQL.
    """
    # Signals
    signals = []
    
    # Flags for SQL criteria
    has_validation = False
    has_intent = False
    has_motivation = False
    
    # Helper to check text content
    def get_text(msg):
        content = msg.get('content', {})
        if content.get('type') == 'text':
            return content.get('text', '').lower()
        return ""

    # Helper to extract name (Basic Regex)
    import re
    def extract_name(text):
        # Patterns for name extraction
        patterns = [
            r"me llamo\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)",
            r"mi nombre es\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)",
            r"soy\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)"
        ]
        
        # Stop words that likely start a new clause after the name
        stop_words = [" y ", " pero ", " que ", " quiero ", " para ", " con ", " en ", " necesito ", " busco ", "."]
        
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                raw_name = match.group(1).strip()
                
                # Cut off at first stop word
                lower_raw = raw_name.lower()
                min_idx = len(raw_name)
                
                for sw in stop_words:
                    idx = lower_raw.find(sw)
                    if idx != -1 and idx < min_idx:
                        min_idx = idx
                
                raw_name = raw_name[:min_idx].strip()
                
                words = raw_name.split()
                if len(words) > 0:
                    # Return reasonable name length (1-3 words usually)
                    return " ".join(words[:3]).title()
        return None

    # 1. Identify Actors & Extract Info
    user_messages = [m for m in messages if m.get('from') == 'user']
    
    # Basic State
    if not user_messages:
        return {
            "chat_id": chat_id,
            "nombre_detectado": "Desconocido",
            "clasificacion": "MQL",
            "razon_principal": "Lead Silencioso (Sin respuesta del usuario).",
            "señales_clave": ["Solo habló el bot/agente"],
            "estado_conversacion": "Sin respuesta inicial"
        }

    # Name Detection Variable
    nombre = "Desconocido"
    last_bot_text = ""

    # 2. Analyze All Messages for Context & Signals
    # We iterate through ALL messages to track context (e.g. what did the bot ask?)
    for msg in messages:
        role = msg.get('from')
        text = get_text(msg)
        content_type = msg.get('content', {}).get('type')
        
        if role in ['bot', 'agent']:
            last_bot_text = text.lower()
            continue
            
        # --- User Message Analysis ---
        
        # Name Detection Logic
        if nombre == "Desconocido":
            # 1. Try Regex first (Explicit: "Me llamo X")
            extracted = extract_name(text)
            if extracted:
                nombre = extracted
                has_validation = True
                signals.append(f"Nombre detectado (Regex): {nombre}")
            
            # 2. Contextual Heuristic (Implicit: Answer to "Con quien tengo el gusto?")
            # Check if previous bot message asked for name
            elif any(q in last_bot_text for q in ["con quién tengo el gusto", "con quien tengo el gusto", "su nombre", "tu nombre", "cómo se llama"]):
                # Check if response looks like a name (short, mostly letters)
                # Heuristic: < 6 words, mostly alphabetic
                words = text.split()
                if 0 < len(words) <= 5:
                    # Assume it's a name
                    # Clean up punctuation
                    clean_name = text.strip().title()
                    # Basic filter: don't capture "Hola", "Buenos dias" as names if they are alone, 
                    # but "Hola soy Juan" is caught by Regex. 
                    # If user says "Juan Perez", we capture it.
                    nombre = clean_name
                    has_validation = True
                    signals.append(f"Nombre detectado (Contexto): {nombre}")

        # A. Validation of Identity
        # Keywords: cédula, dni, id, mi nombre es, soy, ciudad
        if any(kw in text for kw in ["cédula", "dni", "identidad", "cedula", "ciudad"]):
            has_validation = True
            signals.append("Mencionó documento/ubicación (Identity)")
        
        # Image/File sent by user -> Strong signal for payment proof or ID
        if content_type in ['image', 'file']:
            has_validation = True 
            signals.append(f"Envió archivo/imagen ({content_type})")

        # B. Purchase Intent / Budget
        # Keywords: pago, precio, costo, valor, cuenta, deposito, transferencia, link
        if any(kw in text for kw in ["link de pago", "cuenta", "depósito", "transferencia", "pagar", "precio", "costo", "valor"]):
            has_intent = True
            signals.append(f"Palabra clave de intención: '{text[:20]}...'")
        
        if "ya pagué" in text or "listo el pago" in text or "comprobante" in text:
            has_intent = True
            signals.append("Confirmación de pago detectada")

        # C. Professional Motivation
        if any(kw in text for kw in ["trabajo", "ascenso", "profesional", "laboral", "cv", "curriculum", "mejorar"]):
            has_motivation = True
            signals.append("Motivación profesional detectada")
            
    # 3. Determine Classification
    # SQL Requirement: At least 2 of [Validation, Intent, Motivation]
    
    score = sum([has_validation, has_intent, has_motivation])
    classification = "MQL"
    reason = "No cumple criterios suficientes para SQL."
    
    if score >= 2:
        if has_validation:
            classification = "SQL"
            reason = "Cumple con Validación de Identidad + otra señal fuerte."
        else:
            # Score is 2 but missing validation (e.g. Intent + Motivation only)
            classification = "MQL" 
            reason = "Tiene señales de interés pero falta Validación de Identidad obligatoria."
            signals.append("Falta Validación de Identidad")
    else:
        # Specific MQL Sub-cases
        if any(kw in get_text(m) for m in user_messages for kw in ["precio", "info", "hola"]):
             reason = "Consulta básica."
        if any(kw in get_text(m) for m in user_messages for kw in ["caro", "no me interesa", "lo pensaré"]):
             reason = "Objeción detectada."
             signals.append("Objeción explícita")

    # State
    estado = "Activa"
    if not user_messages:
        estado = "Sin respuesta inicial"
    elif "gracias" in get_text(user_messages[-1]) or "adios" in get_text(user_messages[-1]):
        estado = "Abandonada por usuario" # Or closed? Let's stick to simple logic
    
    return {
        "chat_id": chat_id,
        "nombre_detectado": nombre,
        "clasificacion": classification,
        "razon_principal": reason,
        "señales_clave": list(set(signals)), # Dedupe
        "estado_conversacion": estado
    }

def process_data(json_data):
    """
    Main processing function.
    """
    items = json_data.get('items', [])
    grouped_chats = group_and_sort(items)
    
    results = []
    for chat_id, messages in grouped_chats.items():
        result = analyze_conversation(chat_id, messages)
        results.append(result)
        
    return results
