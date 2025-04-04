import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load CSV file (assumes it has 'Date' column and P/Q values)
file_path = "Representative days/DATA.csv"
df = pd.read_csv(file_path)

# Ensure 'Date' column is formatted correctly
df['Date'] = df['Date'].str.strip()

# Identify P and Q columns
P_columns = [col for col in df.columns if col.startswith('P')]
Q_columns = [col for col in df.columns if col.startswith('Q')]

# Convert the P and Q columns to numeric
df[P_columns] = df[P_columns].apply(pd.to_numeric, errors='coerce')
df[Q_columns] = df[Q_columns].apply(pd.to_numeric, errors='coerce')

# Compute the load per building by pairing P and Q columns elementwise
p_values = df[P_columns].values
q_values = df[Q_columns].values
load_per_building = np.sqrt(p_values**2 + q_values**2)
total_load = load_per_building.sum(axis=1)
df['Total_Load'] = total_load

# Select relevant columns: Date, Total_Load, and SUN
formatted_df = df[['Date', 'Total_Load', 'SUN']]
formatted_df.to_csv("formatted_data.csv", index=False)
print("Formatted data saved to formatted_data.csv")

# --- Clustering part ---

# Let's assume that the time series data is hourly.
# Define rolling window size: 3 days = 3 * 24 hours
window_size = 3 * 24

# Create rolling windows of 3 days (each window is a contiguous block of hours)
windows = []
dates = []
for i in range(len(df) - window_size + 1):
    window_data = df.iloc[i:i+window_size]['Total_Load'].values
    if len(window_data) == window_size:
        windows.append(window_data)
        dates.append(df.iloc[i]['Date'])

windows = np.array(windows)

# Standardize the windows data
scaler = StandardScaler()
windows_scaled = scaler.fit_transform(windows)

# Check how many unique windows there are
unique_windows = np.unique(windows_scaled, axis=0)
unique_count = unique_windows.shape[0]
desired_clusters = 10
n_clusters = min(desired_clusters, unique_count)

print(f"Found {unique_count} unique windows. Setting number of clusters to {n_clusters}")

# Perform KMeans clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
clusters = kmeans.fit_predict(windows_scaled)

# Assign clusters back to time windows
cluster_results = pd.DataFrame({'start_date': dates, 'cluster': clusters})
cluster_results.to_csv("clustered_windows.csv", index=False)
print("Clustering completed. Results saved to clustered_windows.csv")
