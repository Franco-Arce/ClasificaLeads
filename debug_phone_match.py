"""
Quick diagnostic script to understand the phone matching issue
"""
import pandas as pd
import re

def normalize_phone(phone):
    if not phone:
        return ""
    return re.sub(r'\D', '', str(phone))

# Load data
neotel_df = pd.read_excel('NotraeUTm/DatabaseQuery_34_30122025_10135276.xls')

# Test phone
test_phone = "593993575726"
norm_test = normalize_phone(test_phone)

print(f"Test phone: {test_phone}")
print(f"Normalized: {norm_test}")
print(f"\n{'='*60}")

# Get phone column
phone_col = 'teltelefono'
print(f"Using phone column: {phone_col}")

# Show some samples from Neotel
print(f"\nSample phones from Neotel (first 10):")
for idx, row in neotel_df.head(10).iterrows():
    raw_phone = row[phone_col]
    normalized = normalize_phone(raw_phone)
    utm = row.get('UTM Medium', 'N/A')
    print(f"  Raw: {raw_phone:20} -> Normalized: {normalized:15} UTM: {utm}")

# Try to find our test phone
neotel_df['normalized_phone'] = neotel_df[phone_col].apply(normalize_phone)
matches = neotel_df[neotel_df['normalized_phone'] == norm_test]

print(f"\n{'='*60}")
print(f"Looking for matches with normalized phone: {norm_test}")
print(f"Matches found: {len(matches)}")

if not matches.empty:
    print("\nMatches:")
    for idx, row in matches.iterrows():
        print(f"  Index: {idx}")
        print(f"  Raw phone: {row[phone_col]}")
        print(f"  UTM Medium: {row.get('UTM Medium', 'N/A')}")
        print(f"  Programa: {row.get('Program aInteres', 'N/A')}")
        print()
else:
    print("\nNo matches found!")
    print("\nLet's check if the phone exists with different formatting:")
    # Check if any phone contains these digits
    for idx, row in neotel_df.iterrows():
        norm_phone = row['normalized_phone']
        if '993575726' in norm_phone:
            print(f"  Found similar: {row[phone_col]} -> {norm_phone}")
            print(f"    UTM Medium: {row.get('UTM Medium', 'N/A')}")
            break
