import pandas as pd

# Load English CLDR data
df = pd.read_excel('cldr_data/english_moderate.xlsx')

print("Looking for y MMM d-d pattern:")
matching_dd = df[df['Winning'].str.contains('y MMM d-d', na=False)]
print(f"Matches for y MMM d-d: {len(matching_dd)}")
if len(matching_dd) > 0:
    print(matching_dd[['English', 'Winning']].head())

print("\nLooking for y MMM yy-yy pattern:")
matching_yy = df[df['Winning'].str.contains('y MMM yy-yy', na=False)]
print(f"Matches for y MMM yy-yy: {len(matching_yy)}")
if len(matching_yy) > 0:
    print(matching_yy[['English', 'Winning']].head())

print("\nLooking for any y MMM pattern:")
matching_ymmm = df[df['Winning'].str.contains('y MMM', na=False)]
print(f"Matches for y MMM: {len(matching_ymmm)}")
if len(matching_ymmm) > 0:
    print(matching_ymmm[['English', 'Winning']].head(10))
