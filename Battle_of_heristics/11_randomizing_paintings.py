import time
import random
import sys
import os
from collections import defaultdict, Counter

DEFAULT_INPUT_PATH = "Data/11_randomizing_paintings.txt"
RANDOM_SEED = 42



def read_input(filename):
    """
    Read and parse the input file containing paintings data.

    Input File Format:
        Line 1: N (integer) - total number of paintings
        Lines 2 to N+1: <orientation> <num_tags> <tag1> <tag2> ... <tagN>

    Args:
        filename (str): Path to the input file.

    Returns:
        list of dict: List of paintings, each represented as a dictionary with keys:
            - 'id' (int): Unique identifier based on line order (0-indexed)
            - 'type' (str): 'L' for landscape, 'P' for portrait
            - 'tags' (set of str): Set of tags describing the painting

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



def create_landscape_frameglasses(paintings):
    """
    Creates frameglasses from landscape paintings.
    Each landscape painting becomes a single frameglass.
    
    Args:
        paintings (list of dict): List of painting dictionaries.
    
    Returns:
        list of dict: Frameglasses with keys 'ids' and 'tags'.
    """
    frameglasses = []
    
    for p in paintings:
        if p['type'] == 'L':
            frameglasses.append({
                'ids': [p['id']],
                'tags': p['tags'].copy()
            })
    
    return frameglasses

def create_portrait_frameglasses(paintings):
    """
    Creates frameglasses from portrait paintings.
    Portraits are paired sequentially into frameglasses.
    If there's an odd number of portraits, the last one is discarded.
    
    Args:
        paintings (list of dict): List of painting dictionaries.
    
    Returns:
        list of dict: Frameglasses with keys 'ids' and 'tags'.
    """
    frameglasses = []
    portraits = [p for p in paintings if p['type'] == 'P']
    
    # Pair portraits sequentially
    for i in range(0, len(portraits) - 1, 2):
        p1 = portraits[i]
        p2 = portraits[i + 1]
        
        frameglasses.append({
            'ids': [p1['id'], p2['id']],
            'tags': p1['tags'].union(p2['tags'])
        })
    
    return frameglasses


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
    landscape_frameglasses = create_landscape_frameglasses(paintings)
    portrait_frameglasses = create_portrait_frameglasses(paintings)
    
    # Combine both types
    all_frameglasses = landscape_frameglasses + portrait_frameglasses
    
    return all_frameglasses


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

def strategy_enhanced_cluster(frameglasses):
    """
    Groups frameglasses by primary tag and orders the resulting clusters by connectivity.

    The algorithm identifies the most frequent (primary) tag for each item, forms clusters
    based on these tags, and orders the clusters greedily to maximize inter-cluster
    connections (starting with the largest). This provides an O(n log n) baseline
    ordering for further refinement.

    Args:
        frameglasses (list of dict): Unsorted list containing 'ids' and 'tags'.

    Returns:
        list of dict: Frameglasses ordered by cluster connectivity.

    """
    if len(frameglasses) <= 1:
        return frameglasses[:]

    # Count tag frequencies globally
    tag_frequency = Counter()
    for fg in frameglasses:
        tag_frequency.update(fg['tags'])

    def get_primary_tag(fg):
        """Determine primary (most frequent) tag for a frameglass."""
        if not fg['tags']:
            return ""
        sorted_tags = sorted(fg['tags'])
        return max(sorted_tags, key=lambda t: (tag_frequency[t], t))

    # Group frameglasses by primary tag
    clusters = defaultdict(list)
    for fg in frameglasses:
        primary = get_primary_tag(fg)
        clusters[primary].append(fg)

    # Sort frameglasses within each cluster deterministically
    for tag in clusters:
        clusters[tag].sort(key=lambda fg: (tuple(sorted(fg['tags'])), tuple(fg['ids'])))

    cluster_keys = list(clusters.keys())
    if len(cluster_keys) <= 1:
        return sum(clusters.values(), [])

    # Order clusters by size (largest first)
    cluster_keys.sort(key=lambda k: len(clusters[k]), reverse=True)
    
    used_clusters = set()
    result = []
    
    # Start with largest cluster
    current_key = cluster_keys[0]
    result.extend(clusters[current_key])
    used_clusters.add(current_key)
    
    # Greedily add clusters with best connection
    while len(used_clusters) < len(cluster_keys):
        last_tags = result[-1]['tags']
        
        best_score = -1
        best_key = None
        
        # Find cluster with best connection to current endpoint
        for key in cluster_keys:
            if key in used_clusters:
                continue
            
            cluster = clusters[key]
            max_connection = max(
                calculate_score(last_tags, fg['tags']) 
                for fg in cluster
            )
            
            if max_connection > best_score:
                best_score = max_connection
                best_key = key
        
        # If no good connection, just pick next available
        if best_key is None:
            for key in cluster_keys:
                if key not in used_clusters:
                    best_key = key
                    break
        
        result.extend(clusters[best_key])
        used_clusters.add(best_key)
    
    return result


def strategy_greedy_best_neighbor(frameglasses, seed=None):
    """
    Builds a sequence by iteratively selecting the best available neighbor.

    Starting from a random frameglass, the algorithm greedily adds the unused item 
    with the highest transition score to the current endpoint. This O(n²) approach 
    is fast but sensitive to the starting point and prone to local optima.

    Args:
        frameglasses (list of dict): Frameglasses to order.
        seed (int or None): Random seed for the starting point.

    Returns:
        list of dict: Ordered frameglasses.
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

    # Greedily build sequence
    for _ in range(n - 1):
        current = result[-1]
        current_tags = current['tags']
        best_score = -1
        best_idx = -1

        # Find best next frameglass
        for i in range(n):
            if used[i]:
                continue

            fg_tags = frameglasses[i]['tags']
            common = len(current_tags & fg_tags)
            diff1 = len(current_tags) - common
            diff2 = len(fg_tags) - common
            score = min(common, diff1, diff2)

            if score > best_score:
                best_score = score
                best_idx = i

        result.append(frameglasses[best_idx])
        used[best_idx] = True

    return result


def strategy_multiple_random_greedy(frameglasses, seed=None, num_attempts=3):
    """
    Multi-start greedy: run greedy algorithm multiple times and keep best result.
    
    This strategy overcomes the local optima problem of single greedy runs by
    trying multiple different starting points and selecting the best outcome.
    
    Args:
        frameglasses (list of dict): Frameglasses to order
        seed (int or None): Base random seed
        num_attempts (int): Number of greedy runs (default: 3)
    
    Returns:
        list of dict: Best ordering found across all attempts
    
    Time Complexity: O(k × n²) where k is num_attempts
    """
    if seed is None:
        seed = RANDOM_SEED

    best_result = []
    best_score = -1

    for i in range(num_attempts):
        result = strategy_greedy_best_neighbor(frameglasses, seed=seed + i)
        score = calculate_global_score(result)

        if score > best_score:
            best_score = score
            best_result = result

    return best_result


def strategy_window_optimization(initial_order, window_size=200):
    """
    Refines the ordering by sliding overlapping windows and re-optimizing locally.

    Slides a window (default size 200, 50% overlap) across the sequence. Each window 
    is re-optimized using multi-start greedy (or clustering if > 5000 items) to improve 
    local scores while maintaining smooth transitions.

    Args:
        initial_order (list of dict): Initial sequence of frameglasses.
        window_size (int): Size of sliding window (default: 200).

    Returns:
        list of dict: Refined ordering.

    Complexity:
        Time: O(w × n × k) | w=window_size, n=total_items, k=iterations
    """
    result = initial_order[:]
    n = len(result)
    
    if n < window_size:
        return result
    
    # Slide overlapping windows
    for start in range(0, n - window_size, window_size // 2):
        end = min(start + window_size, n)
        window = result[start:end]
        
        # Re-optimize window
        if len(window) < 5000:
            optimized_window = strategy_multiple_random_greedy(window, num_attempts=3)
        else:
            optimized_window = strategy_enhanced_cluster(window)
        
        # Calculate score improvement
        if start > 0:
            old_score = calculate_score(result[start-1]['tags'], result[start]['tags'])
            new_score = calculate_score(result[start-1]['tags'], optimized_window[0]['tags'])
        else:
            old_score = 0
            new_score = 0
        
        old_score += sum(
            calculate_score(result[i]['tags'], result[i+1]['tags'])
            for i in range(start, end - 1)
        )
        
        new_score += sum(
            calculate_score(optimized_window[i]['tags'], optimized_window[i+1]['tags'])
            for i in range(len(optimized_window) - 1)
        )
        
        if end < n:
            old_score += calculate_score(result[end-1]['tags'], result[end]['tags'])
            new_score += calculate_score(optimized_window[-1]['tags'], result[end]['tags'])
        
        # Accept if improvement
        if new_score > old_score:
            result[start:end] = optimized_window
    
    return result


def strategy_2opt(initial_order, max_iterations=5, check_every=20):
    """
    Performs local search optimization (2-Opt) by swapping pairs of frameglasses.

    Iteratively attempts to swap element pairs within a local range (50) to improve 
    connectivity. Uses sparse sampling (checking every `check_every` position) 
    for efficiency on large datasets.

    Args:
        initial_order (list of dict): Initial ordering of frameglasses.
        max_iterations (int): Max passes (default: 5).
        check_every (int): Sampling rate for efficiency (default: 20).

    Returns:
        list of dict: Polished ordering with local improvements.

    Complexity:
        Time: O(k * n^2 / s) | Space: O(1) (in-place)
        """
    result = initial_order[:]
    n = len(result)
    
    if n < 4:
        return result
    
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        # Sparse sampling for efficiency
        for i in range(0, n - 3, check_every):
            for j in range(i + 2, min(i + 50, n - 1)):
                # Calculate score before swap (only affected transitions)
                score_before = 0
                if i > 0:
                    score_before += calculate_score(result[i-1]['tags'], result[i]['tags'])
                score_before += calculate_score(result[i]['tags'], result[i+1]['tags'])
                if j < n - 1:
                    score_before += calculate_score(result[j]['tags'], result[j+1]['tags'])
                if j > i + 1:
                    score_before += calculate_score(result[j-1]['tags'], result[j]['tags'])
                
                # Perform swap
                result[i], result[j] = result[j], result[i]
                
                # Calculate score after swap
                score_after = 0
                if i > 0:
                    score_after += calculate_score(result[i-1]['tags'], result[i]['tags'])
                score_after += calculate_score(result[i]['tags'], result[i+1]['tags'])
                if j < n - 1:
                    score_after += calculate_score(result[j]['tags'], result[j+1]['tags'])
                if j > i + 1:
                    score_after += calculate_score(result[j-1]['tags'], result[j]['tags'])
                
                # Keep swap if improved
                if score_after > score_before:
                    improved = True
                else:
                    # Revert swap
                    result[i], result[j] = result[j], result[i]
    
    return result


def running_algorithm(frameglasses):
    print("   Step 1/3: Enhanced clustering...")
    result = strategy_enhanced_cluster(frameglasses)
    
    print("   Step 2/3: Window optimization...")
    result = strategy_window_optimization(result, window_size=200)
    
    print("   Step 3/3: 2-Opt enhancement...")
    result = strategy_2opt(result, max_iterations=5, check_every=20)
    
    return result


def main(input_file, output_file):
    """
    Main execution function for the three-phase optimization algorithm.
    """
    print(f"Reading: {input_file}")
    start_time = time.time()
    
    paintings = read_input(input_file)
    print(f"Loaded {len(paintings):,} paintings")
    
    print("Creating frameglasses...")
    frameglasses = create_frameglasses(paintings)
    print(f"Created {len(frameglasses):,} frameglasses")
    
    print("\nRunning algorithm...")
    random.seed(RANDOM_SEED)
    ordered_frames = running_algorithm(frameglasses)
    
    score = calculate_global_score(ordered_frames)
    elapsed = time.time() - start_time
    
    print(f"\nScore: {score:,}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"{'='*60}")
    
    print(f"\nWriting: {output_file}")
    write_output(output_file, ordered_frames)
    print("Done!")
    
    return score


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = DEFAULT_INPUT_PATH if len(sys.argv) < 2 else sys.argv[1]
        name_without_ext = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"./Outputs/submission_{name_without_ext}.txt"

    main(input_file, output_file)