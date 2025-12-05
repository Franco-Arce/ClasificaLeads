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
    has_strong_intent = False
    has_motivation = False
    program_not_offered = False
    
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
    
    # Extract Phone Number from the first message's chat info (it's consistent across the chat)
    # The structure is item['chat']['contactId'] based on the JSON check
    telefono = ""
    if messages:
        telefono = messages[0].get('chat', {}).get('contactId', "")

    # Basic State
    if not user_messages:
        return {
            "chat_id": chat_id,
            "telefono": telefono,
            "clasificacion": "MQL",
            "razon_principal": "Lead Silencioso (Sin respuesta del usuario).",
            "señales_clave": ["Solo habló el bot/agente"],
            "estado_conversacion": "Sin respuesta inicial"
        }

    last_bot_text = ""

    # 2. Analyze All Messages for Context & Signals
    # We iterate through ALL messages to track context (e.g. what did the bot ask?)
    for msg in messages:
        role = msg.get('from')
        text = get_text(msg)
        content_type = msg.get('content', {}).get('type')
        
        if role in ['bot', 'agent']:
            if "no estamos ofreciendo ese tipo de programas" in text:
                program_not_offered = True
                signals.append("Bot indicó programa no ofrecido")
            last_bot_text = text.lower()
            continue
            
        # --- User Message Analysis ---
        
        # A. Validation of Identity - REMOVED as per user request
        # We no longer require name or identity validation.
        
        # Image/File sent by user -> Strong signal for payment proof or ID
        if content_type in ['image', 'file']:
            has_validation = True 
            signals.append(f"Envió archivo/imagen ({content_type})")

        # B. Purchase Intent / Budget
        # Split into Strong (Payment) and Weak (Price)
        
        # Strong Intent: Payment, Transfer, Account, Link
        if any(kw in text for kw in ["link de pago", "cuenta", "depósito", "transferencia", "pagar", "comprobante"]):
            has_intent = True
            has_strong_intent = True
            signals.append(f"Intención de PAGO detectada: '{text[:20]}...'")
            
        if "ya pagué" in text or "listo el pago" in text:
            has_intent = True
            has_strong_intent = True
            signals.append("Confirmación de pago explícita")

        # Weak Intent: Price, Cost, Value (Interest but not commitment)
        if any(kw in text for kw in ["precio", "costo", "valor", "info", "información"]):
            has_intent = True
            # Do not set has_strong_intent
            signals.append(f"Consulta de precio/info: '{text[:20]}...'")

        # C. Professional Motivation
        # Keywords: trabajo, ascenso, profesional, laboral, cv, curriculum, mejorar, crecimiento
        motivation_keywords = [
            "trabajo", "ascenso", "profesional", "laboral", "cv", "curriculum", "mejorar", 
            "crecimiento", "personal", "aprender", "actualizado", "requerimiento",
            "empleo", "puesto", "cargo", "superación", "conocimiento", "carrera", "estudio"
        ]
        
        # Specific phrases provided by user
        motivation_phrases = [
            "mejorar perfil profesional",
            "crecimiento personal",
            "mantenerme actualizado",
            "requerimiento laboral",
            "mejorar en mi trabajo"
        ]

        # 1. Explicit keywords/phrases in text
        if any(phrase in text for phrase in motivation_phrases) or any(kw in text for kw in motivation_keywords):
            has_motivation = True
            signals.append("Motivación profesional detectada (Keywords)")
            
        # 2. Contextual: Answer to "Principal motivación"
        elif any(q in last_bot_text for q in ["motivación", "motivo", "interés", "por qué", "por que"]):
             if len(text.split()) > 2: # meaningful response
                 has_motivation = True
                 signals.append("Motivación detectada (Respuesta a pregunta)")
            
    # 3. Determine Classification
    # New Rules (User Request):
    # - Identity (Name) is NOT required.
    # - Motivation ALONE is sufficient for SQL.
    # - Strong Intent (Payment) ALONE is sufficient for SQL.
    
    classification = "MQL"
    reason = "Consulta estándar o falta de señales fuertes."
    
    if program_not_offered:
        classification = "MQL"
        reason = "Programa no ofrecido (Excepción)."
    elif has_motivation:
        classification = "SQL"
        reason = "Motivación profesional/personal detectada (Criterio Fuerte)."
    elif has_strong_intent:
        classification = "SQL"
        reason = "Intención de PAGO detectada (Criterio Fuerte)."
    else:
        # Specific MQL Sub-cases
        if any(kw in get_text(m) for m in user_messages for kw in ["caro", "no me interesa", "lo pensaré"]):
             reason = "Objeción detectada."
             signals.append("Objeción explícita")

    # State
    estado = "Activa"
    if not user_messages:
        estado = "Sin respuesta inicial"
    elif "gracias" in get_text(user_messages[-1]) or "adios" in get_text(user_messages[-1]):
        estado = "Abandonada por usuario" # Or closed? Let's stick to simple logic

    # Calculate metrics
    mensajes_usuario = len(user_messages)
    
    duracion_chat = "0:00:00"
    if messages:
        try:
            # Sort just in case, though group_and_sort should have done it
            sorted_msgs = sorted(messages, key=lambda x: x.get('creationTime', ''))
            start_time_str = sorted_msgs[0].get('creationTime', '').replace('Z', '+00:00')
            end_time_str = sorted_msgs[-1].get('creationTime', '').replace('Z', '+00:00')
            
            if start_time_str and end_time_str:
                start_dt = datetime.fromisoformat(start_time_str)
                end_dt = datetime.fromisoformat(end_time_str)
                duration = end_dt - start_dt
                # Format as Days, HH:MM:SS
                days = duration.days
                seconds_in_day = duration.seconds
                hours = seconds_in_day // 3600
                minutes = (seconds_in_day % 3600) // 60
                seconds = seconds_in_day % 60
                
                if days > 0:
                    duracion_chat = f"{days} días, {hours:02}:{minutes:02}:{seconds:02}"
                else:
                    duracion_chat = f"{hours:02}:{minutes:02}:{seconds:02}"
        except Exception as e:
            print(f"Error calculating duration for chat {chat_id}: {e}")
            pass

    return {
        "chat_id": chat_id,
        "telefono": telefono,
        "clasificacion": classification,
        "razon_principal": reason,
        "señales_clave": list(set(signals)), # Dedupe
        "estado_conversacion": estado,
        "duracion_chat": duracion_chat,
        "mensajes_usuario": mensajes_usuario
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
