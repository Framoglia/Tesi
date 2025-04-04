import pandas as pd
import numpy as np

# Load CSV file
file_path = "Representative days/DATA.csv"
df = pd.read_csv(file_path)

# Ensure 'Date' column is formatted correctly
df['Date'] = df['Date'].str.strip()

# Identify P and Q columns
P_columns = [col for col in df.columns if col.startswith('P')]
Q_columns = [col for col in df.columns if col.startswith('Q')]

# Convert the P and Q columns to numeric (if they aren't already)
df[P_columns] = df[P_columns].apply(pd.to_numeric, errors='coerce')
df[Q_columns] = df[Q_columns].apply(pd.to_numeric, errors='coerce')

# Compute the load per building by pairing P and Q columns elementwise
p_values = df[P_columns].values  # shape (n_samples, 37)
q_values = df[Q_columns].values  # shape (n_samples, 37)
# Calculate sqrt(P^2 + Q^2) for each building
load_per_building = np.sqrt(p_values**2 + q_values**2)
# Sum the load for all buildings
total_load = load_per_building.sum(axis=1)
df['Total_Load'] = total_load

# Select relevant columns: Date, Total_Load, and SUN
formatted_df = df[['Date', 'Total_Load', 'SUN']]

# Save to a new CSV
formatted_df.to_csv("formatted_data.csv", index=False)

print("Formatted data saved to formatted_data.csv")
