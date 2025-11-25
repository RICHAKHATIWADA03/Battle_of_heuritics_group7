import time
import random
import sys
import os

DEFAULT_INPUT_PATH = "Data/10_computable_moments.txt"
RANDOM_SEED = 42


def read_input(filename):
    """
    Reads the input file containing paintings data.

    Args:
        filename (str): Path to the input file.

    Returns:
        list of dict: List of paintings, each represented as a dictionary with keys:
            - 'id' (int): Unique identifier based on line order.
            - 'type' (str): 'L' for landscape, 'P' for portrait.
            - 'tags' (set of str): Set of tags describing the painting.

    Raises:
        SystemExit: If file not found or reading error occurs.
    """
    paintings = []

    try:
        with open(filename, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines[1:]):
            parts = line.strip().split()
            if not parts:
                continue

            orientation = parts[0]
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
    Writes the ordered frameglasses to the output file.

    Args:
        filename (str): Path of the output file.
        ordered_frameglasses (list of dict): Ordered frameglasses with 'ids' key.

    Raises:
        SystemExit: If write operation fails.
    """
    try:
        with open(filename, 'w') as f:
            f.write(f"{len(ordered_frameglasses)}\n")

            for fg in ordered_frameglasses:
                ids_str = " ".join(map(str, fg['ids']))
                f.write(f"{ids_str}\n")

    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


def create_frameglasses(paintings):
    """
    Creates frameglasses from paintings.
    
    - Each landscape becomes a single frameglass
    - Portraits are paired sequentially into frameglasses
    - Odd portrait (if any) is discarded

    Args:
        paintings (list of dict): List of painting dictionaries.

    Returns:
        list of dict: Frameglasses with keys 'ids' and 'tags'.
    """
    landscapes = [p for p in paintings if p['type'] == 'L']
    portraits = [p for p in paintings if p['type'] == 'P']

    frameglasses = []

    # Convert landscapes
    for p in landscapes:
        frameglasses.append({
            'ids': [p['id']],
            'tags': p['tags'].copy()
        })

    # Pair portraits
    for i in range(0, len(portraits) - 1, 2):
        p1 = portraits[i]
        p2 = portraits[i + 1]

        frameglasses.append({
            'ids': [p1['id'], p2['id']],
            'tags': p1['tags'].union(p2['tags'])
        })

    return frameglasses


def calculate_score(tags1, tags2):
    """
    Calculates the transition score between two frameglasses.

    Score formula:
        score = min(common_tags, tags_only_in_first, tags_only_in_second)

    Args:
        tags1 (set): Tags from first frameglass.
        tags2 (set): Tags from second frameglass.

    """
    common = len(tags1 & tags2)
    only_in_first = len(tags1 - tags2)
    only_in_second = len(tags2 - tags1)

    return min(common, only_in_first, only_in_second)


def calculate_global_score(ordered_frameglasses):
    """
    Calculates total score for an ordered sequence of frameglasses.

    Args:
        ordered_frameglasses (list of dict): Ordered frameglasses.

    Returns:
        int: Sum of all transition scores between consecutive frameglasses.
    """
    if len(ordered_frameglasses) < 2:
        return 0

    total_score = 0
    for i in range(len(ordered_frameglasses) - 1):
        score = calculate_score(
            ordered_frameglasses[i]['tags'],
            ordered_frameglasses[i + 1]['tags']
        )
        total_score += score

    return total_score


def greedy_best_neighbor(frameglasses, seed=None):
    """
    Constructs an ordering using greedy best-neighbor selection.
    
    Algorithm:
        1. Start from a random frameglass
        2. At each step, find the unused frameglass with best score
        3. Add it to the sequence and mark as used
        4. Repeat until all frameglasses are ordered
    
    Time Complexity: O(n²) where n is number of frameglasses
    Space Complexity: O(n)

    Args:
        frameglasses (list of dict): List of frameglasses to order.
        seed (int or None): Random seed for reproducibility.

    Returns:
        list of dict: Ordered list of frameglasses.
    """
    n = len(frameglasses)
    if n <= 1:
        return frameglasses[:]

    if seed is not None:
        random.seed(seed)
    else:
        random.seed(RANDOM_SEED)

    used = [False] * n
    result = []

    # Start from random frameglass
    start_idx = random.randint(0, n - 1)
    result.append(frameglasses[start_idx])
    used[start_idx] = True

    # Greedily build the sequence
    for _ in range(n - 1):
        current_tags = result[-1]['tags']
        best_score = -1
        best_idx = -1

        # Find best next frameglass
        for i in range(n):
            if used[i]:
                continue

            score = calculate_score(current_tags, frameglasses[i]['tags'])

            if score > best_score:
                best_score = score
                best_idx = i

        result.append(frameglasses[best_idx])
        used[best_idx] = True

    return result


def multi_start_greedy(frameglasses, seed=None, num_attempts=5):
    """
    
    Strategy:
        - Run greedy algorithm with different random starting points
        - Each attempt uses a different random seed
        - Keep track of the best solution found
        - Return the ordering with highest score
    
    Why it works:
        - Different starting points explore different regions of solution space
        - Overcomes local optima that single greedy run might get stuck in
        - Balances quality with computational efficiency
    
    Time Complexity: O(k × n²) where k is num_attempts
    
    Args:
        frameglasses (list of dict): List of frameglasses to order.
        seed (int or None): Base random seed.
        num_attempts (int): Number of greedy attempts to run (default 5).

    Returns:
        list of dict: Best ordering found across all attempts.
    """
    if seed is None:
        seed = RANDOM_SEED

    best_result = []
    best_score = -1

    for i in range(num_attempts):
        # Run greedy with different seed
        result = greedy_best_neighbor(frameglasses, seed=seed + i)
        score = calculate_global_score(result)

        # Keep best result
        if score > best_score:
            best_score = score
            best_result = result

    return best_result


def main(input_file, output_file, num_attempts=5):
    """
    Main execution function for the frameglass ordering algorithm.
    
    Process:
        1. Parse input file to load paintings
        2. Convert paintings to frameglasses
        3. Apply multi-start greedy algorithm
        4. Calculate and display satisfaction score
        5. Write ordered result to output file
    
    Args:
        input_file (str): Path to input file with painting data.
        output_file (str): Path where ordered output will be saved.
        num_attempts (int): Number of greedy attempts (default 5).
   
    """
    print("=" * 60)
    print("Multi-Start Greedy Algorithm")
    print("=" * 60)
    print(f"Reading: {input_file}")
    start_time = time.time()
    
    # FIXED: Call read_input instead of parse_input_file
    paintings = read_input(input_file)
    print(f"Loaded {len(paintings):,} paintings")
    
    print("Creating frameglasses...")
   
    frameglasses = create_frameglasses(paintings)
    print(f"Created {len(frameglasses):,} frameglasses")
    
    print(f"Ordering frameglasses ({num_attempts} attempts)...")

    random.seed(RANDOM_SEED)
    ordered_frames = multi_start_greedy(frameglasses, seed=RANDOM_SEED, num_attempts=num_attempts)

    score = calculate_global_score(ordered_frames)
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"Score: {score:,}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"{'='*60}")
    
    print(f"\nWriting: {output_file}")
 
    write_output(output_file, ordered_frames)
    print("Done!\n")
    
    return score


if __name__ == '__main__':
    """
    Command-line interface for the frameglass ordering program.
    
    Usage:
        python script.py <input_file> <output_file> [num_attempts]
    """
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    else:
     
        input_file = DEFAULT_INPUT_PATH

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
     
        base_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = f"./Outputs/submission_{name_without_ext}.txt"

    if len(sys.argv) >= 4:
        num_attempts = int(sys.argv[3])
    else:
        num_attempts = 5

    main(input_file, output_file, num_attempts)