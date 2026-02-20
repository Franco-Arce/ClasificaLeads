"""
Test script to verify UTM Medium extraction from Neotel Excel file
"""
import pandas as pd
from logic import match_neotel_data

# Load the Neotel file
neotel_df = pd.read_excel('NotraeUTm/DatabaseQuery_34_30122025_10135276.xls')

print("=== NEOTEL DATA LOADED ===")
print(f"Total records: {len(neotel_df)}")
print(f"\nColumns: {neotel_df.columns.tolist()}\n")

# Normalize phones
from logic import normalize_phone
neotel_df['normalized_phone'] = neotel_df['teltelefono'].apply(normalize_phone)

# Show sample UTM Medium values
print("=== UTM MEDIUM VALUES IN FILE ===")
print(neotel_df['UTM Medium'].value_counts(dropna=False))
print()

# Test with a phone that has UTM data
test_phone = neotel_df[neotel_df['UTM Medium'].notna()].iloc[0]['teltelefono']
test_date = neotel_df[neotel_df['UTM Medium'].notna()].iloc[0]['Fecha Insert Lead']

print(f"=== TESTING WITH PHONE: {test_phone} ===")
print(f"Expected UTM Medium: {neotel_df[neotel_df['teltelefono'] == test_phone].iloc[0]['UTM Medium']}")
print()

# Call the function
result = match_neotel_data(test_phone, str(test_date), neotel_df)

print("=== EXTRACTION RESULT ===")
for key, value in result.items():
    print(f"{key}: {value}")
    
# Verify
if result.get('utm_medium'):
    print("\n[SUCCESS] UTM Medium was extracted correctly!")
else:
    print(f"\n[FAILED] Expected '{expected_utm}' but got '{result['utm_medium']}'")
    
print("\n" + "="*50)
