
import time
import random
import sys
import os


DEFAULT_INPUT_PATH = "Data/0_example.txt"
RANDOM_SEED = 42  # Set seed for reproducibility

def read_input(filename):
    """
    Reads the input file and returns a list of painting dictionaries.
    
    Args:
        filename: Path to the input file
        
    Returns:
        List of dicts: {'id': int, 'type': 'L' or 'P', 'tags': set()}
    """
    paintings = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # First line is the number of paintings (we skip it, use enumerate instead)
        for i, line in enumerate(lines[1:]):
            parts = line.strip().split()
            if not parts:
                continue
            
            orientation = parts[0]
            # parts[1] is the tag count, we don't need it
            tags = set(parts[2:])
            
            paintings.append({
                'id': i,
                'type': orientation,
                'tags': tags
            })
            
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    return paintings


def write_output(filename, ordered_frameglasses):
    """
    Writes the submission file in the required format.
    
    Args:
        filename: Output file path
        ordered_frameglasses: List of frameglass dictionaries in order
    """
    try:
        with open(filename, 'w') as f:
            # First line: number of frameglasses
            f.write(f"{len(ordered_frameglasses)}\n")
            
            # Following lines: painting IDs for each frameglass
            for fg in ordered_frameglasses:
                ids_str = " ".join(map(str, fg['ids']))
                f.write(f"{ids_str}\n")
                
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


def separate_paintings_by_type(paintings):
    """
    Separates paintings into landscapes and portraits.
    
    Args:
        paintings: List of painting dictionaries
        
    Returns:
        Tuple of (landscapes, portraits) lists
    """
    landscapes = [p for p in paintings if p['type'] == 'L']
    portraits = [p for p in paintings if p['type'] == 'P']
    
    return landscapes, portraits


def create_landscape_frameglasses(landscapes):
    """
    Creates frameglasses from landscape paintings (1 per frameglass).
    
    Args:
        landscapes: List of landscape painting dictionaries
        
    Returns:
        List of frameglass dictionaries
    """
    frameglasses = []
    
    for p in landscapes:
        frameglasses.append({
            'ids': [p['id']],
            'tags': p['tags'].copy(),
            'type': 'L'
        })
        
    return frameglasses


def create_portrait_frameglasses(portraits):
    """
    Creates frameglasses from portrait paintings (2 per frameglass).
    Pairs portraits sequentially.
    
    Args:
        portraits: List of portrait painting dictionaries
        
    Returns:
        List of frameglass dictionaries
    """
    frameglasses = []
    
    # Pair portraits sequentially
    for i in range(0, len(portraits) - 1, 2):
        p1 = portraits[i]
        p2 = portraits[i + 1]
        
        # Union of tags from both portraits
        combined_tags = p1['tags'].union(p2['tags'])
        
        frameglasses.append({
            'ids': [p1['id'], p2['id']],
            'tags': combined_tags,
            'type': 'P'
        })
    
    return frameglasses


def create_frameglasses(paintings):
    """
    Groups all paintings into frameglasses.
    Rule: 1 Landscape OR 2 Portraits per frameglass.
    
    Args:
        paintings: List of painting dictionaries
        
    Returns:
        List of frameglass dictionaries
    """
    # Separate by type
    landscapes, portraits = separate_paintings_by_type(paintings)
    
    # Create frameglasses for each type
    landscape_fgs = create_landscape_frameglasses(landscapes)
    portrait_fgs = create_portrait_frameglasses(portraits)
    
    # Combine all frameglasses
    all_frameglasses = landscape_fgs + portrait_fgs
    
    return all_frameglasses



def calculate_local_score(fg1, fg2):
    """
    Calculates Local Robotic Satisfaction between two frameglasses.
    
    Score = min(common_tags, tags_only_in_fg1, tags_only_in_fg2)
    
    Args:
        fg1: First frameglass dictionary
        fg2: Second frameglass dictionary
        
    Returns:
        Integer score
    """
    tags1 = fg1['tags']
    tags2 = fg2['tags']
    
    # Count of common tags
    common = len(tags1.intersection(tags2))
    
    # Count of tags in fg1 but not in fg2
    only_in_fg1 = len(tags1.difference(tags2))
    
    # Count of tags in fg2 but not in fg1
    only_in_fg2 = len(tags2.difference(tags1))
    
    return min(common, only_in_fg1, only_in_fg2)


def calculate_global_score(ordered_frameglasses):
    """
    Calculates Global Robotic Satisfaction for the entire sequence.
    Sum of all local scores between consecutive frameglasses.
    
    Args:
        ordered_frameglasses: List of frameglasses in display order
        
    Returns:
        Total integer score
    """
    if len(ordered_frameglasses) < 2:
        return 0
    
    total_score = 0
    
    for i in range(len(ordered_frameglasses) - 1):
        local_score = calculate_local_score(
            ordered_frameglasses[i], 
            ordered_frameglasses[i + 1]
        )
        total_score += local_score
        
    return total_score


def strategy_preserve_order(frameglasses):
    """
    Strategy 1: Keep original order.
    
    Args:
        frameglasses: List of frameglass dictionaries
        
    Returns:
        Copy of frameglasses in original order
    """
    return frameglasses[:]


def strategy_reverse_order(frameglasses):
    """
    Strategy 2: Reverse the order.
    
    Args:
        frameglasses: List of frameglass dictionaries
        
    Returns:
        Copy of frameglasses in reverse order
    """
    return frameglasses[::-1]


def strategy_random_order(frameglasses, seed=None):
    """
    Strategy 3: Random shuffle.
    
    Args:
        frameglasses: List of frameglass dictionaries
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Randomly shuffled copy of frameglasses
    """
    if seed is not None:
        random.seed(seed)
    
    shuffled = frameglasses[:]
    random.shuffle(shuffled)
    
    return shuffled


def strategy_sort_by_tag_count(frameglasses, reverse=True):
    """
    Strategy 4: Sort by number of tags.
    
    Args:
        frameglasses: List of frameglass dictionaries
        reverse: If True, sort descending (most tags first)
        
    Returns:
        Sorted copy of frameglasses
    """
    return sorted(
        frameglasses, 
        key=lambda fg: len(fg['tags']), 
        reverse=reverse
    )


def strategy_sort_by_tag_count_ascending(frameglasses):
    """
    Strategy 5: Sort by number of tags (ascending - fewest first).
    
    Args:
        frameglasses: List of frameglass dictionaries
        
    Returns:
        Sorted copy of frameglasses
    """
    return strategy_sort_by_tag_count(frameglasses, reverse=False)


def set_random_seed(seed):
    """
    Sets the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value
    """
    random.seed(seed)
    print(f"Random seed set to: {seed}")


def get_input_file_path(argv):
    """
    Gets input file path from command line arguments or default.
    
    Args:
        argv: Command line arguments (sys.argv)
        
    Returns:
        Path to input file
    """
    if len(argv) > 1:
        return argv[1]
    return DEFAULT_INPUT_PATH


def generate_output_filename(input_file):
    """
    Generates output filename based on input filename.
    
    Args:
        input_file: Path to input file
        
    Returns:
        Output filename string
    """
    base_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(base_name)[0]
    return f"submission_{name_without_ext}.txt"


def print_header(input_file):
    """
    Prints processing header information.
    
    Args:
        input_file: Path to input file being processed
    """
    print("=" * 50)
    print("HCW - Heuristics Challenge Week Solution")
    print("=" * 50)
    print(f"Processing: {input_file}")
    print()


def print_results_table_header():
    """Prints the results table header."""
    print(f"{'Strategy':<25} | {'Score':<10} | {'Time (s)':<10}")
    print("-" * 50)


def print_results_table_row(name, score, duration):
    """
    Prints a single row in the results table.
    
    Args:
        name: Strategy name
        score: Achieved score
        duration: Execution time in seconds
    """
    print(f"{name:<25} | {score:<10} | {duration:.6f}")


def print_winner(strategy_name, score):
    """
    Prints the winning strategy information.
    
    Args:
        strategy_name: Name of the best strategy
        score: Best score achieved
    """
    print("-" * 50)
    print(f"Winner: {strategy_name}")
    print(f"Best Score: {score}")
    print("-" * 50)


def run_all_strategies(frameglasses, seed=RANDOM_SEED):
    """
    Runs all ordering strategies and returns results.
    
    Args:
        frameglasses: List of frameglass dictionaries
        seed: Random seed for reproducible random strategy
        
    Returns:
        Tuple of (best_order, best_score, best_strategy_name)
    """
    # Define all strategies to test
    strategies = [
        ("Original Order", lambda fg: strategy_preserve_order(fg)),
        ("Reverse Order", lambda fg: strategy_reverse_order(fg)),
        ("Random Order", lambda fg: strategy_random_order(fg, seed)),
        ("Sort by Tags (Desc)", lambda fg: strategy_sort_by_tag_count(fg, True)),
        ("Sort by Tags (Asc)", lambda fg: strategy_sort_by_tag_count_ascending(fg)),
    ]
    
    best_score = -1
    best_order = []
    best_strategy_name = ""
    
    print_results_table_header()
    
    for name, strategy_func in strategies:
        # Time the strategy
        t_start = time.time()
        current_order = strategy_func(frameglasses)
        score = calculate_global_score(current_order)
        t_end = time.time()
        
        duration = t_end - t_start
        
        # Print results
        print_results_table_row(name, score, duration)
        
        # Track best
        if score > best_score:
            best_score = score
            best_order = current_order
            best_strategy_name = name
    
    return best_order, best_score, best_strategy_name


def main():
    """Main function to run the HCW solution."""
    
    # Get input file
    input_file = get_input_file_path(sys.argv)
    
    # Check file exists
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        print("Usage: python kcw_solution.py <path_to_input_file>")
        return
    
    # Print header
    print_header(input_file)
    
    # Set random seed for reproducibility
    set_random_seed(RANDOM_SEED)
    
    print("Step 1: Parsing input file...")
    start_time = time.time()
    
    paintings = read_input(input_file)
    
    parse_time = time.time() - start_time
    print(f"  - Loaded {len(paintings)} paintings")
    print(f"  - Parse time: {parse_time:.4f}s")
    print()
 
    print("Step 2: Creating frameglasses...")
    start_time = time.time()
    
    frameglasses = create_frameglasses(paintings)
    
    create_time = time.time() - start_time
    
    landscapes, portraits = separate_paintings_by_type(paintings)
    print(f"  - Landscapes: {len(landscapes)}")
    print(f"  - Portraits: {len(portraits)} (paired into {len(portraits)//2} frameglasses)")
    print(f"  - Total frameglasses: {len(frameglasses)}")
    print(f"  - Creation time: {create_time:.4f}s")
    print()
    print("Step 3: Testing ordering strategies...")
    print()
    
    best_order, best_score, best_strategy_name = run_all_strategies(
        frameglasses, 
        seed=RANDOM_SEED
    )
    
    print()
    print_winner(best_strategy_name, best_score)
    
    print()
    print("Step 4: Writing output file...")
    
    output_filename = generate_output_filename(input_file)
    write_output(output_filename, best_order)
    
    print(f"  - Output saved to: {output_filename}")
    print()
    print("Done!")
    print("=" * 50)


if __name__ == "__main__":
    main()