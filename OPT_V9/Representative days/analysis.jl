using RepresentativePeriodsFinder, Cbc, YAML, CSV, DataFrames

# Load configuration
config = YAML.load_file("config.yml")

# Validate data format
df = CSV.read(config["time_series"]["default"]["source"], DataFrame)
println("Data loaded with size: ", size(df))

# Run the optimization
result = find_representative_periods(
    config,
    optimizer=Cbc.Optimizer,
    optimizer_attributes=(seconds=3600,),  # 1 hour timeout
)

# Process results
println("Selected period starts at indices: ", result.selected_periods)
println("Objective value: ", result.objective_value)

# Save binary vector
binary_vector = zeros(Int, nrow(df))
for start_idx in result.selected_periods
    binary_vector[start_idx:start_idx+95] .= 1  # 96-hour periods
end

CSV.write("representative_periods.csv", DataFrame(Selected=binary_vector))