import pandas as pd
import matplotlib.pyplot as plt

# Define colors for districts
district_colors = {"A": "red", "B": "blue", "C": "green"}

# Define markers for different types
type_markers = {
    "HV_sub": "s",   # Square
    "MV_sub": "D",   # Diamond
    "LV_sub": "^",   # Triangle
    "MV_load": "o",  # Circle
    "LV_load": "x"   # X
}

# Load data from CSV
file_path = "Mycampus.csv"
df = pd.read_csv(file_path)

# Fix column names (remove spaces)
df.columns = df.columns.str.strip()

# Strip spaces from all relevant columns
df["District"] = df["District"].fillna("Unknown").astype(str).str.strip()
df["Type"] = df["Type"].fillna("Unknown").astype(str).str.strip()
df["Position"] = df["Position"].astype(str).str.strip()

# Debugging: Print unique values
print("Unique Districts:", df["District"].unique())
print("Unique Types:", df["Type"].unique())

# Extract coordinates and convert to float (Handle negative numbers as well)
df[['X', 'Y']] = df['Position'].str.extract(r'\((-?\d+);(-?\d+)\)').astype(float)

# Drop rows with NaN values in essential columns (Position, District, Type)
df = df.dropna(subset=["Position", "District", "Type"])

# Plot
plt.figure(figsize=(10, 8))

for _, row in df.iterrows():
    x, y = row["X"], row["Y"]
    bus_type = row["Type"]
    district = row["District"]

    # Get marker and color (default to black circle if missing)
    marker = type_markers.get(bus_type, "o")
    color = district_colors.get(district, "black")

    plt.scatter(x, y, c=color, marker=marker)

# Define custom handles for the legend
handles = [plt.Line2D([0], [0], marker=marker, color='w', markerfacecolor='black', markersize=10, label=key) for key, marker in type_markers.items()]
plt.legend(handles=handles, loc="upper right")

# Labels & Title
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.title("Campus Electrical Network")
plt.grid(True)
plt.show()

