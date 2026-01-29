import json
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import re

def normalize_phone(phone):
    """
    Normalizes phone number by removing non-digit characters.
    Handles float values (e.g., 593993575726.0) by converting to int first.
    """
    if not phone:
        return ""
    
    # Handle pandas NaN/NaT
    if pd.isna(phone):
        return ""
    
    # If it's a float, convert to int first to remove .0
    try:
        if isinstance(phone, float):
            phone = int(phone)
    except (ValueError, OverflowError):
        pass
    
    # Remove all non-digit characters
    return re.sub(r'\D', '', str(phone))

def match_neotel_data(chat_phone, chat_date_str, neotel_df):
    """
    Finds the best match in Neotel data for a given phone and date.
    Returns a dictionary with UTM data.
    """
    if neotel_df is None or neotel_df.empty or not chat_phone:
        return {}

    norm_chat_phone = normalize_phone(chat_phone)
    if not norm_chat_phone:
        return {}
        
    # Filter by phone
    phone_col = None
    possible_cols = ['TELWHATSAPP', 'teltelefono', 'TELTELEFONO', 'num_telefono']
    
    for col in possible_cols:
        if col in neotel_df.columns:
            phone_col = col
            break
            
    if not phone_col:
        for col in neotel_df.columns:
            if 'telefono' in col.lower():
                phone_col = col
                break
                
    if not phone_col:
        return {}

    if 'normalized_phone' not in neotel_df.columns:
         neotel_df['normalized_phone'] = neotel_df[phone_col].apply(normalize_phone)

    matches = neotel_df[neotel_df['normalized_phone'] == norm_chat_phone]
    
    if matches.empty:
        return {}
        
    if len(matches) == 1:
        best_match = matches.iloc[0]
    else:
        best_match = None
        try:
            chat_dt = pd.to_datetime(chat_date_str)
            if chat_dt.tzinfo:
                chat_dt = chat_dt.tz_convert(None)
        except:
            best_match = matches.iloc[0]
            
        date_col = 'Fecha Insert Lead'
        if date_col not in matches.columns:
             if 'Fecha Inserción Leads' in matches.columns:
                 date_col = 'Fecha Inserción Leads'
             else:
                 best_match = matches.iloc[0]
        
        if best_match is None:     
            min_diff = timedelta(days=365*10)
            
            for idx, row in matches.iterrows():
                try:
                    neotel_dt = row[date_col]
                    if not isinstance(neotel_dt, datetime):
                        neotel_dt = pd.to_datetime(neotel_dt)
                    
                    if neotel_dt.tzinfo:
                        neotel_dt = neotel_dt.tz_convert(None)
                        
                    diff = abs(chat_dt - neotel_dt)
                    if diff < min_diff:
                        min_diff = diff
                        best_match = row
                except Exception as e:
                    continue
                    
            if best_match is None:
                best_match = matches.iloc[0]
            
    def clean_val(val):
        if pd.isna(val) or val is pd.NaT:
            return ""
        return str(val)
    
    def safe_get(series_row, col_name, default=''):
        try:
            if col_name in series_row.index:
                return series_row[col_name]
            return default
        except:
            return default

    utm_source = safe_get(best_match, 'UTM Source', safe_get(best_match, 'Canal', ''))
    utm_medium = safe_get(best_match, 'UTM Medium', '')
    utm_origen = safe_get(best_match, 'UTM Origen', safe_get(best_match, 'Medio', ''))
    programa_interes = safe_get(best_match, 'Program aInteres', '')
    # Try multiple column name variants for Resolución (encoding issues)
    resolucion = ''
    resolucion_cols = ['Resolución', 'Resolucion', 'Resolución', 'RESOLUCION']
    for col in resolucion_cols:
        if col in best_match.index:
            resolucion = best_match[col]
            break
    
    return {
        "utm_source": clean_val(utm_source),
        "utm_medium": clean_val(utm_medium),
        "utm_origen": clean_val(utm_origen),
        "programa_interes": clean_val(programa_interes),
        "resolucion": clean_val(resolucion)
    }


def group_and_sort(items):
    """
    Groups items by chatId and sorts them by creationTime.
    """
    grouped = defaultdict(list)
    for item in items:
        chat_id = item.get('chat', {}).get('chatId')
        if chat_id:
            grouped[chat_id].append(item)
    
    for chat_id in grouped:
        grouped[chat_id].sort(key=lambda x: x.get('creationTime', ''))
        
    return grouped


# ============================================================================
# NUEVO SISTEMA DE SCORING
# ============================================================================

def check_spam(messages, user_messages):
    """
    Verifica si el lead debe clasificarse como SPAM.
    Retorna (is_spam, razon) si es SPAM, (False, None) si no lo es.
    
    Condiciones SPAM:
    - Lead declara no haber dejado sus datos
    - Datos de contacto inválidos
    - Respuesta hostil, incoherente o sin sentido
    """
    signals = []
    
    # Keywords que indican que no dejó sus datos
    no_data_keywords = [
        "no dejé mis datos", "no deje mis datos",
        "no solicité", "no solicite",
        "no pedí", "no pedi",
        "no me inscribí", "no me inscribi",
        "número equivocado", "numero equivocado",
        "no soy", "se equivocaron",
        "no es mi número", "no es mi numero",
        "no di mis datos", "no proporcioné", "no proporcione"
    ]
    
    # Keywords que indican respuesta hostil o incoherente
    hostile_keywords = [
        "déjame en paz", "dejame en paz",
        "no me molesten", "dejen de molestar",
        "spam", "acoso", "denunciar",
        "voy a denunciar", "bloqueado",
        "idiota", "estúpido", "estupido",
        "maldito", "basura", "porquería"
    ]
    
    # Patrones de respuestas incoherentes (muy cortas o sin sentido)
    incoherent_patterns = [
        r'^[a-z]{1,2}$',  # Una o dos letras sueltas
        r'^[0-9]{1,2}$',  # Uno o dos números sueltos
        r'^\.+$',         # Solo puntos
        r'^[?!]+$',       # Solo signos de puntuación
    ]
    
    for msg in user_messages:
        text = get_message_text(msg).lower()
        
        # Verificar si declara no haber dejado datos
        for kw in no_data_keywords:
            if kw in text:
                return True, f"Lead declara no haber dejado sus datos: '{kw}'"
        
        # Verificar respuestas hostiles
        for kw in hostile_keywords:
            if kw in text:
                return True, f"Respuesta hostil detectada: '{kw}'"
        
        # Verificar respuestas incoherentes (solo si es el único mensaje)
        if len(user_messages) == 1 and len(text) < 5:
            for pattern in incoherent_patterns:
                if re.match(pattern, text.strip()):
                    return True, "Respuesta incoherente o sin sentido"
    
    return False, None


def calculate_motivation_score(messages, user_messages):
    """
    Calcula el puntaje de motivación del lead (hasta 40 puntos).
    
    +25: Motivación profesional clara
    +15: Impacto laboral concreto
    +5:  Motivación vaga
    0:   Sin motivación declarada
    -10: Objeciones tempranas
    """
    score = 0
    signals = []
    has_professional_motivation = False
    
    # Keywords de motivación profesional clara (+25)
    professional_motivation_keywords = [
        "trabajo", "ascenso", "profesional", "laboral",
        "crecer", "crecimiento", "reconvertir", "reconversión",
        "actualización", "actualizarme", "actualizado",
        "mejorar perfil", "mejorar profesional",
        "superación", "carrera profesional",
        "brochure", "me interesa mucho", "muy interesado",
        "necesito capacitarme", "quiero especializarme",
        # Nuevas variantes agregadas
        "capacitarme", "capacitación", "capacitacion", 
        "formarme", "formación", "formacion",
        "entrenamiento", "entrenarme"
    ]
    
    # Keywords de impacto laboral concreto (+15)
    labor_impact_keywords = [
        "puesto", "salario", "sueldo", "aumento",
        "empresa", "promoción", "ascender",
        "jefe", "gerente", "director",
        "cv", "curriculum", "currículum",
        "conseguir empleo", "buscar trabajo", "nuevo trabajo"
    ]
    
    # Keywords de motivación vaga (+5)
    vague_motivation_keywords = [
        "me interesa aprender", "quiero aprender",
        "me gustaría saber", "me gustaria saber",
        "por curiosidad", "solo información", "solo informacion",
        # Consultas activas (muestran interés)
        "consultar por", "quisiera consultar", "quiero consultar",
        "información sobre", "informacion sobre",
        "me interesa", "estoy interesado", "estoy interesada"
    ]
    
    # Keywords de objeciones tempranas (-10)
    early_objection_keywords = [
        "no me interesa", "solo miro", "solo mirando",
        "no estoy interesado", "no estoy seguro",
        "tal vez después", "tal vez despues",
        "quizás más adelante", "quizas mas adelante",
        "no sé", "no se", "no estoy buscando"
    ]
    
    all_user_text = " ".join([get_message_text(msg).lower() for msg in user_messages])
    
    # Verificar motivación profesional clara (+25)
    for kw in professional_motivation_keywords:
        if kw in all_user_text:
            if not has_professional_motivation:
                score += 25
                has_professional_motivation = True
                signals.append(f"Motivación profesional clara: '{kw}'")
            break
    
    # Verificar impacto laboral concreto (+15) - Solo si no tiene motivación profesional
    if not has_professional_motivation:
        for kw in labor_impact_keywords:
            if kw in all_user_text:
                score += 15
                signals.append(f"Impacto laboral concreto: '{kw}'")
                break
    else:
        # Si ya tiene motivación profesional, agregar +15 si también menciona impacto laboral
        for kw in labor_impact_keywords:
            if kw in all_user_text:
                score += 15
                signals.append(f"Impacto laboral adicional: '{kw}'")
                break
    
    # Verificar motivación vaga (+5) - Solo si no tiene otras motivaciones
    if score == 0:
        for kw in vague_motivation_keywords:
            if kw in all_user_text:
                score += 5
                signals.append(f"Motivación vaga: '{kw}'")
                break
    
    # Verificar objeciones tempranas (-10)
    for kw in early_objection_keywords:
        if kw in all_user_text:
            score -= 10
            signals.append(f"Objeción temprana: '{kw}'")
            break
    
    # Cap score at 40
    score = min(score, 40)
    
    return score, signals, has_professional_motivation


def calculate_payment_score(messages, user_messages):
    """
    Calcula el puntaje de intención y capacidad de pago (hasta 30 puntos).
    
    +30: Puede pagar / evalúa invertir
    +20: Consulta formas de pago o cuotas
    +5:  Pregunta solo precio sin compromiso
    -15: Objeción de precio
    -30: Declara que no va a pagar
    """
    score = 0
    signals = []
    has_payment_intent = False
    
    # Keywords de intención de pago (+30)
    payment_intent_keywords = [
        "pago", "pagar", "transferencia", "comprobante",
        "cuenta", "depósito", "deposito", "depositar",
        "tarjeta", "cupón", "cupon",
        "ya pagué", "ya pague", "listo el pago",
        "voy a pagar", "quiero pagar", "cómo pago", "como pago",
        "envié el pago", "envie el pago",
        "link de pago", "enlace de pago",
        # Nuevas variantes de inscripción (implica pago)
        "inscribirme", "inscripción", "inscripcion", 
        "matricularme", "matrícula", "matricula",
        "reservar cupo", "reserva de cupo"
    ]
    
    # Keywords de consulta de formas de pago (+20)
    payment_forms_keywords = [
        "cuotas", "financiamiento", "financiar",
        "formas de pago", "métodos de pago", "metodos de pago",
        "pago en cuotas", "a plazos", "plazo",
        "pueden financiar", "hay descuento", "descuentos",
        "beca", "becas", "ayuda financiera",
        # Preguntas sobre inicio (indica planificación de inscripción)
        "cuando inicia", "cuándo inicia", "cuando empieza", "cuándo empieza",
        "fecha de inicio", "próximo inicio", "proximo inicio",
        "inicio de clases", "inicio del programa", "inicio del diplomado", "inicio de diplomados", "inicio del curso", "inicio de"
    ]
    
    # Keywords de consulta de precio (+5)
    price_inquiry_keywords = [
        "precio", "costo", "valor", "cuánto cuesta", "cuanto cuesta",
        "cuánto vale", "cuanto vale", "inversión", "inversion",
        "qué precio", "que precio"
    ]
    
    # Keywords de objeción de precio (-15)
    price_objection_keywords = [
        "caro", "muy caro", "costoso", "no puedo pagar",
        "no tengo dinero", "no tengo plata",
        "no me interesa", "por ahora no", "más adelante", "mas adelante",
        "lo pensaré", "lo pensare", "tengo que pensar",
        "no es para mí", "no es para mi",
        "otro momento", "después veo", "despues veo"
    ]
    
    # Keywords de declaración de no pagar (-30)
    no_pay_keywords = [
        "no voy a pagar", "no pagaré", "no pagare",
        "gratis", "no tengo para pagar",
        "no puedo invertir", "imposible pagar",
        "fuera de mi presupuesto", "no me alcanza"
    ]
    
    all_user_text = " ".join([get_message_text(msg).lower() for msg in user_messages])
    
    # Verificar intención de pago (+30)
    for kw in payment_intent_keywords:
        if kw in all_user_text:
            score += 30
            has_payment_intent = True
            signals.append(f"Intención de pago: '{kw}'")
            break
    
    # Verificar consulta de formas de pago (+20) - Solo si no tiene intención de pago directa
    if not has_payment_intent:
        for kw in payment_forms_keywords:
            if kw in all_user_text:
                score += 20
                has_payment_intent = True
                signals.append(f"Consulta formas de pago: '{kw}'")
                break
    
    # Verificar consulta de precio (+5) - Solo si no tiene otras señales positivas
    if score == 0:
        for kw in price_inquiry_keywords:
            if kw in all_user_text:
                score += 5
                signals.append(f"Consulta de precio: '{kw}'")
                break
    
    # Verificar declaración de no pagar (-30) - Tiene prioridad sobre objeción
    no_pay_found = False
    for kw in no_pay_keywords:
        if kw in all_user_text:
            score -= 30
            no_pay_found = True
            signals.append(f"Declara no pagar: '{kw}'")
            break
    
    # Verificar objeción de precio (-15) - Solo si no declaró que no pagará
    if not no_pay_found:
        for kw in price_objection_keywords:
            if kw in all_user_text:
                score -= 15
                signals.append(f"Objeción de precio: '{kw}'")
                break
    
    # Cap score at 30 (can be negative)
    score = min(score, 30)
    
    return score, signals, has_payment_intent


def calculate_behavior_score(messages, user_messages):
    """
    Calcula el puntaje de comportamiento y timing (hasta 30 puntos).
    
    +20: Respuesta < 8 horas
    +10: Respuesta entre 8 y 24 horas
    +5:  Respuesta > 24 horas
    +10: Inicia conversación / seguimiento activo
    -10: No responde (ghosting)
    """
    score = 0
    signals = []
    
    # Si no hay mensajes del usuario, es ghosting
    if not user_messages:
        score -= 10
        signals.append("No responde (ghosting)")
        return score, signals
    
    # Calcular tiempo de respuesta
    # Buscar el primer mensaje del bot y el primer mensaje del usuario después
    first_bot_time = None
    first_user_response_time = None
    
    for msg in messages:
        role = msg.get('from')
        creation_time = msg.get('creationTime', '')
        
        if role in ['bot', 'agent'] and first_bot_time is None:
            try:
                first_bot_time = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            except:
                pass
        elif role == 'user' and first_bot_time is not None and first_user_response_time is None:
            try:
                first_user_response_time = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            except:
                pass
            break
    
    # Calcular diferencia de tiempo
    if first_bot_time and first_user_response_time:
        response_time = first_user_response_time - first_bot_time
        hours = response_time.total_seconds() / 3600
        
        if hours < 8:
            score += 20
            signals.append(f"Respuesta rápida: < 8 horas ({hours:.1f}h)")
        elif hours < 24:
            score += 10
            signals.append(f"Respuesta moderada: 8-24 horas ({hours:.1f}h)")
        else:
            score += 5
            signals.append(f"Respuesta lenta: > 24 horas ({hours:.1f}h)")
    else:
        # Si el usuario inició la conversación
        if messages and messages[0].get('from') == 'user':
            score += 10
            signals.append("Usuario inició la conversación")
    
    # Verificar si el usuario hace seguimiento activo (envía múltiples mensajes)
    if len(user_messages) >= 3:
        score += 10
        signals.append("Seguimiento activo (múltiples mensajes)")
    
    # Verificar si el usuario inició la conversación
    if messages and messages[0].get('from') == 'user':
        if "Usuario inició la conversación" not in signals:
            score += 10
            signals.append("Usuario inició la conversación")
    
    # Cap score at 30
    score = min(score, 30)
    
    return score, signals


def get_message_text(msg):
    """Helper to safely extract text from a message."""
    content = msg.get('content', {})
    if content.get('type') == 'text':
        return content.get('text', '')
    return ""


def analyze_conversation(chat_id, messages):
    """
    Analiza una conversación para clasificar el lead usando el nuevo sistema de scoring.
    
    Sistema:
    - SPAM: Score = 0 (reglas excluyentes)
    - MQL: Score 1-49
    - SQL: Score 50-100
    
    Regla prioritaria: Motivación profesional + Intención de pago = SQL
    """
    # Identificar mensajes del usuario
    user_messages = [m for m in messages if m.get('from') == 'user']
    
    # Extraer teléfono
    telefono = ""
    if messages:
        telefono = messages[0].get('chat', {}).get('contactId', "")
    
    # Si no hay mensajes del usuario, es SPAM (ghosting = score 0 = SPAM)
    if not user_messages:
        return {
            "chat_id": chat_id,
            "telefono": telefono,
            "clasificacion": "SPAM",
            "score_total": 0,
            "score_motivacion": 0,
            "score_pago": 0,
            "score_comportamiento": 0,
            "razon_principal": "Lead sin respuesta (Ghosting) - Score 0",
            "señales_clave": ["Solo habló el bot/agente", "Sin respuesta del usuario"],
            "estado_conversacion": "Sin respuesta"
        }
    
    # 1. VERIFICAR SPAM (Regla excluyente)
    is_spam, spam_reason = check_spam(messages, user_messages)
    if is_spam:
        return {
            "chat_id": chat_id,
            "telefono": telefono,
            "clasificacion": "SPAM",
            "score_total": 0,
            "score_motivacion": 0,
            "score_pago": 0,
            "score_comportamiento": 0,
            "razon_principal": spam_reason,
            "señales_clave": ["SPAM detectado"],
            "estado_conversacion": "Descartado"
        }
    
    # 2. CALCULAR SCORES
    all_signals = []
    
    # Score de motivación (hasta 40 puntos)
    motivation_score, motivation_signals, has_professional_motivation = calculate_motivation_score(messages, user_messages)
    all_signals.extend(motivation_signals)
    
    # Score de intención de pago (hasta 30 puntos)
    payment_score, payment_signals, has_payment_intent = calculate_payment_score(messages, user_messages)
    all_signals.extend(payment_signals)
    
    # Score de comportamiento (hasta 30 puntos)
    behavior_score, behavior_signals = calculate_behavior_score(messages, user_messages)
    all_signals.extend(behavior_signals)
    
    # 3. CALCULAR SCORE TOTAL
    total_score = motivation_score + payment_score + behavior_score
    
    # Asegurar que el score esté entre 1 y 100 (no 0, porque 0 = SPAM)
    total_score = max(1, min(total_score, 100))
    
    # 4. APLICAR REGLA PRIORITARIA
    # Si tiene motivación profesional clara (+25) Y intención de pago (+30 o +20), es SQL
    priority_rule_applied = False
    if has_professional_motivation and has_payment_intent:
        priority_rule_applied = True
        all_signals.append("⭐ REGLA PRIORITARIA: Motivación + Pago = SQL")
    
    # 5. DETERMINAR CLASIFICACIÓN
    if priority_rule_applied:
        classification = "SQL"
        reason = "Regla prioritaria: Motivación profesional clara + Intención de pago"
    elif total_score >= 50:
        classification = "SQL"
        reason = f"Score alto ({total_score}/100) - Derivar a Ventas"
    else:
        classification = "MQL"
        reason = f"Score moderado ({total_score}/100) - Nurturing/Maduración"
    
    # 6. DETERMINAR ESTADO DE CONVERSACIÓN
    estado = "Activa"
    last_user_text = get_message_text(user_messages[-1]).lower() if user_messages else ""
    if "gracias" in last_user_text or "adios" in last_user_text or "adiós" in last_user_text:
        estado = "Cerrada por usuario"
    
    # 7. CALCULAR DURACIÓN
    duracion_chat = "0:00:00"
    if messages:
        try:
            sorted_msgs = sorted(messages, key=lambda x: x.get('creationTime', ''))
            start_time_str = sorted_msgs[0].get('creationTime', '').replace('Z', '+00:00')
            end_time_str = sorted_msgs[-1].get('creationTime', '').replace('Z', '+00:00')
            
            if start_time_str and end_time_str:
                start_dt = datetime.fromisoformat(start_time_str)
                end_dt = datetime.fromisoformat(end_time_str)
                duration = end_dt - start_dt
                
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
            pass
    
    return {
        "chat_id": chat_id,
        "telefono": telefono,
        "clasificacion": classification,
        "score_total": total_score,
        "score_motivacion": motivation_score,
        "score_pago": payment_score,
        "score_comportamiento": behavior_score,
        "razon_principal": reason,
        "señales_clave": list(set(all_signals)),
        "estado_conversacion": estado,
        "duracion_chat": duracion_chat,
        "mensajes_usuario": len(user_messages)
    }


def process_data(json_data, neotel_df=None):
    """
    Función principal de procesamiento.
    """
    items = json_data.get('items', [])
    grouped_chats = group_and_sort(items)
    
    # Pre-process Neotel DF if provided
    if neotel_df is not None and not neotel_df.empty:
        phone_col = None
        possible_cols = ['TELWHATSAPP', 'teltelefono', 'TELTELEFONO', 'num_telefono']
        
        for col in possible_cols:
            if col in neotel_df.columns:
                phone_col = col
                break

        if not phone_col:
            for col in neotel_df.columns:
                if 'telefono' in col.lower():
                    phone_col = col
                    break

        if phone_col:
            neotel_df['normalized_phone'] = neotel_df[phone_col].apply(normalize_phone)
            
            date_col = 'Fecha Insert Lead'
            if date_col not in neotel_df.columns:
                if 'Fecha Inserción Leads' in neotel_df.columns:
                    date_col = 'Fecha Inserción Leads'
            
            if date_col in neotel_df.columns:
                neotel_df[date_col] = pd.to_datetime(neotel_df[date_col], errors='coerce')
    
    results = []
    for chat_id, messages in grouped_chats.items():
        result = analyze_conversation(chat_id, messages)
        
        # Enrich with Neotel Data
        if neotel_df is not None and not neotel_df.empty:
            start_time_str = ""
            if messages:
                sorted_msgs = sorted(messages, key=lambda x: x.get('creationTime', ''))
                start_time_str = sorted_msgs[0].get('creationTime', '')
                
            utm_data = match_neotel_data(result.get('telefono'), start_time_str, neotel_df)
            result.update(utm_data)
            
        # Ensure keys exist
        for key in ['utm_source', 'utm_medium', 'utm_origen', 'programa_interes', 'resolucion']:
            if key not in result:
                result[key] = ""
            
        results.append(result)
        
    return results
