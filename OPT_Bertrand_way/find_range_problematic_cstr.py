import re

def parse_lp_constraints(lp_file_path, min_threshold=1e-4, max_threshold=1e6):
    """
    Parses a .lp file to find constraint names with coefficients outside [min_threshold, max_threshold].

    Parameters:
        lp_file_path (str): Path to the .lp file.
        min_threshold (float): Minimum acceptable absolute coefficient.
        max_threshold (float): Maximum acceptable absolute coefficient.

    Returns:
        dict: A dictionary mapping constraint names to lists of (coefficient, variable) pairs that are outside the range.
    """
    constraints_outside_range = {}
    current_constraint = None

    # Regular expression patterns
    constraint_header_pattern = re.compile(r'^\s*([^\s:]+)\s*:')
    term_pattern = re.compile(r'([+-]?\s*\d*\.?\d+(?:[eE][+-]?\d+)?)\s*([a-zA-Z_][a-zA-Z0-9_().]*)')
    constraint_end_pattern = re.compile(r'^\s*[<>=]=?\s*[\d.eE+-]+')

    with open(lp_file_path, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            if line.strip().startswith('\\') or not line.strip():
                continue
                
            # Check if it's the start of a new constraint
            header_match = constraint_header_pattern.match(line)
            if header_match:
                current_constraint = header_match.group(1)
                continue
                
            # Check if it's the end of a constraint (with =, <=, >=)
            if constraint_end_pattern.match(line):
                current_constraint = None
                continue
                
            # Process terms if we're in a constraint
            if current_constraint:
                for coeff_str, var in term_pattern.findall(line):
                    try:
                        # Clean and parse the coefficient
                        coeff = float(coeff_str.replace(" ", ""))
                        if abs(coeff) < min_threshold or abs(coeff) > max_threshold:
                            if current_constraint not in constraints_outside_range:
                                constraints_outside_range[current_constraint] = []
                            constraints_outside_range[current_constraint].append((coeff, var))
                    except ValueError:
                        # Skip if coefficient can't be parsed
                        continue

    return constraints_outside_range

if __name__ == "__main__":
    path_to_lp = "model.lp"
    min_thresh = 0.001
    max_thresh = 100000000

    bad_constraints = parse_lp_constraints(path_to_lp, min_thresh, max_thresh)

    print("Constraints with extreme coefficients:")
    for name, terms in sorted(bad_constraints.items()):
        print(f"\nConstraint: {name}")
        for coeff, var in terms:
            print(f"  - Coefficient: {coeff:g} (variable: {var})")