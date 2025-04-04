using CSV, DataFrames, Statistics

function main()
    println("Loading data...")
    df = CSV.read("DATA.csv", DataFrame)
    data = Matrix(df[:, 2:end])  # Skip first column (dates)
    
    println("Finding representative periods...")
    binary_vec, selected = simple_rep_periods(data, 4, 96)
    
    # Save results
    results = DataFrame(
        DateTime=df[!,1], 
        Selected=binary_vec,
        IsRepresentative=[any(i .∈ (s:s+95 for s in selected) for i in 1:size(data,1))]
    )
    CSV.write("results.csv", results)
    
    println("\nSelected period starting rows:", selected)
    return results
end

function simple_rep_periods(data::Matrix, n_periods::Int, period_length::Int)
    # 1. Normalize data
    μ = mean(data, dims=1)
    σ = std(data, dims=1)
    norm_data = (data .- μ) ./ σ
    
    # 2. Calculate distances between all possible periods
    n = size(data,1)
    distances = zeros(n, n)
    
    for i in 1:n, j in 1:n
        # Handle edge cases where period would go past end of data
        len_i = min(period_length, n-i+1)
        len_j = min(period_length, n-j+1)
        min_len = min(len_i, len_j)
        
        # Only compare overlapping portions
        diff = norm_data[i:i+min_len-1,:] - norm_data[j:j+min_len-1,:]
        distances[i,j] = sum(diff.^2)
    end
    
    # 3. Greedy selection
    selected = Int[]
    remaining = collect(1:n)
    
    while length(selected) < n_periods && !isempty(remaining)
        if isempty(selected)
            push!(selected, rand(remaining))
        else
            scores = [maximum(distances[i,selected]) for i in remaining]
            push!(selected, remaining[argmin(scores)])
        end
        # Remove selected and nearby periods
        filter!(x -> all(abs.(x .- selected) .> period_length), remaining)
    end
    
    # 4. Create binary vector
    binary_vec = zeros(Int, n)
    for s in selected
        binary_vec[s:min(s+period_length-1,n)] .= 1
    end
    
    return binary_vec, selected
end

# Run it
main()