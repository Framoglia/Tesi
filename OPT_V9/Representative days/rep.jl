using Pkg

# 1. Create a clean environment
Pkg.activate("RepPeriodEnv"; shared=true)
Pkg.Registry.add("General")  # Ensure standard registry exists

# 2. Install required packages with version checks
try
    # Try installing from GitLab
    Pkg.add(url="https://gitlab.kuleuven.be/UCM/representativedaysfinder.jl")
    
    # Check if installed correctly
    using RepresentativePeriodsFinder
    @info "Package installed successfully!"
    
catch e
    @warn "Failed to install RepresentativePeriodsFinder. Attempting fallback..."
    
    # Fallback to standard packages
    Pkg.add(["CSV", "DataFrames", "Dates", "Statistics", "Clustering", "Cbc"])
    
    @info """If you still want the original package, please:
    1. Update Julia: run 'juliaup update' in your terminal
    2. Restart Julia
    3. Run this script again"""
end
