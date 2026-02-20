import json
import os

base_path = r"c:\Users\franc\OneDrive\Escritorio\Mis Cosas\Proyectos\Nods\ClasificaLeads\AnalizarClasificacion"
json_1 = os.path.join(base_path, "bulk_export_nodslabsas-whatsapp-593998348706_2026-02-12.json")
json_2 = os.path.join(base_path, "bulk_export_nodslabsas-whatsapp-593998348706_2026-02-12 (1).json")

target_phones = ["593997090163", "593968409232"]

output_file = "conversations_mql.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for json_path in [json_1, json_2]:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        
        for phone in target_phones:
            # Get all messages for this phone (from ALL roles)
            phone_msgs = [i for i in items if i.get('chat', {}).get('contactId') == phone]
            
            if not phone_msgs:
                continue
            
            phone_msgs.sort(key=lambda x: x.get('creationTime', ''))
            
            out.write(f"\n{'='*80}\n")
            out.write(f"TELEFONO: {phone}\n")
            out.write(f"ARCHIVO: {os.path.basename(json_path)}\n")
            out.write(f"TOTAL MENSAJES: {len(phone_msgs)}\n")
            out.write(f"{'='*80}\n\n")
            
            for msg in phone_msgs:
                role = msg.get('from', '?')
                time = msg.get('creationTime', '')[:19]
                content = msg.get('content', {})
                content_type = content.get('type', '?')
                
                if content_type == 'text':
                    text = content.get('text', '')
                elif content_type == 'image':
                    text = f"[IMAGEN: {content.get('url', 'sin url')[:60]}...]"
                elif content_type == '__unsupported__':
                    text = "[CONTENIDO NO SOPORTADO]"
                else:
                    text = f"[{content_type}]"
                
                out.write(f"[{time}] [{role.upper():6s}] {text}\n")
            
            out.write("\n")

print(f"Conversaciones extraidas en {output_file}")
