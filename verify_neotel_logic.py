
import pandas as pd
from logic import process_data
from datetime import datetime
import json

def test_neotel_integration():
    print("Testing Neotel Integration Logic...")

    # 1. Create Mock Neotel DataFrame matching the file structure
    data = {
        'teltelefono': [593991234567, '998765432'],
        'Fecha Insert Lead': [
            pd.Timestamp('2025-12-01 10:00:00'),
            pd.Timestamp('2025-12-02 11:30:00')
        ],
        'UTM Medium': ['social', 'email'],
        'Canal': ['facebook', 'newsletter'], # Fallback for Source
        'Medio': ['cpc', 'organic'], # Fallback for Origen
        'Program aInteres': ['Derecho Digital', 'MBA']
    }
    neotel_df = pd.DataFrame(data)
    print("Mock Neotel Data:")
    print(neotel_df)

    # 2. Create Mock Chat Data
    # Chat 1 matches first row (Phone match)
    # Chat 2 matches second row (Phone match)
    # Chat 3 no match
    
    mock_chat_data = {
        "items": [
            {
                "chat": {"chatId": "chat1", "contactId": "593991234567"},
                "from": "user",
                "creationTime": "2025-12-01T10:05:00Z",
                "content": {"type": "text", "text": "Hola, info precio"}
            },
             {
                "chat": {"chatId": "chat2", "contactId": "998765432"},
                "from": "user",
                "creationTime": "2025-12-02T12:00:00Z",
                "content": {"type": "text", "text": "Hola"}
            },
            {
                "chat": {"chatId": "chat3", "contactId": "111111111"},
                "from": "user",
                "creationTime": "2025-12-03T09:00:00Z",
                "content": {"type": "text", "text": "Hola"}
            }
        ]
    }

    # 3. Run Process Data
    print("\nProcessing Data...")
    results = process_data(mock_chat_data, neotel_df)
    
    # 4. Verify Results
    print("\nResults:")
    for res in results:
        print(f"Chat: {res['chat_id']}, Phone: {res['telefono']}")
        print(f"  UTM Source: {res.get('utm_source')}")
        print(f"  UTM Medium: {res.get('utm_medium')}")
        print(f"  UTM Origen: {res.get('utm_origen')}")
        print(f"  Programa Interes: {res.get('programa_interes')}")
        
        if res['chat_id'] == 'chat1':
            assert res['utm_medium'] == 'social', "Chat 1 UTM Medium Mismatch"
            assert res['utm_source'] == 'facebook', "Chat 1 UTM Source (Canal) Mismatch"
            assert res['programa_interes'] == 'Derecho Digital', "Chat 1 Programa Interes Mismatch"
            
        if res['chat_id'] == 'chat2':
            assert res['utm_medium'] == 'email', "Chat 2 UTM Medium Mismatch"
            assert res['programa_interes'] == 'MBA', "Chat 2 Programa Interes Mismatch"
            
        if res['chat_id'] == 'chat3':
             assert res['utm_medium'] == '', "Chat 3 should correspond to empty"

    print("\nSUCCESS: All tests passed!")

if __name__ == "__main__":
    test_neotel_integration()
