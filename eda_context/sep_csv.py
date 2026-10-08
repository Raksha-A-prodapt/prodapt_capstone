import pandas as pd

# Input CSV
input_file = "D:/raksha/capstone/try2/data/5g_netops.csv"

# Output CSV
output_file = "telecom_network_incidents_with_id.csv"

# Read the original CSV
df = pd.read_csv(input_file)

# Add Incident_ID as the first column
df.insert(
    0,
    "Incident_ID",
    [f"INC{i:06d}" for i in range(1, len(df) + 1)]
)

# Save as a separate CSV
df.to_csv(output_file, index=False)

print(f"Created: {output_file}")
print(f"Rows: {len(df)}")
print(df[["Incident_ID"]].head())
print(df[["Incident_ID"]].tail())