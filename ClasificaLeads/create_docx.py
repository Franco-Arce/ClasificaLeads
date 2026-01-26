import docx
import json

data = {
  "items": [
    {
      "id": "DOCX_MSG_001",
      "creationTime": "2025-11-18T10:00:00.000Z",
      "from": "user",
      "content": { "type": "text", "text": "Hola, soy DOCX User." },
      "chat": { "chatId": "CHAT_DOCX_TEST" }
    }
  ]
}

doc = docx.Document()
doc.add_paragraph(json.dumps(data))
doc.save('test_docx.docx')
print("Created test_docx.docx")
