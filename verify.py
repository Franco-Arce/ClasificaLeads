import json
from logic import process_data

def verify():
    with open('test_user_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    results = process_data(data)
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    verify()
