import pandas as pd

def filter_csv(input_file, output_file):
    # Read CSV file
    df = pd.read_csv(input_file)
    
    # Filter rows where 'lines' column equals 23
    filtered_df = df[df['lines'] == 23]
    
    # Save the filtered dataframe to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    
# Example usage
input_csv = "optimal_values.csv"  # Change this to your actual input file
output_csv = "filtered_output.csv"
filter_csv(input_csv, output_csv)
print(f"Filtered CSV saved as {output_csv}")