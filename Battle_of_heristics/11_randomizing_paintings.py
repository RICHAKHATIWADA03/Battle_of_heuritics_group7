import time
import random
import sys
import os
from collections import defaultdict, Counter

DEFAULT_INPUT_PATH = "Data/11_randomizing_paintings.txt"  # Default input file path
RANDOM_SEED = 42


def read_input(filename):
    paintings = []
    try:
        with open(filename, 'r') as f:
            next(f)
            for i, line in enumerate(f):
                parts = line.split()
                if parts:
                    paintings.append({
                        'id': i,
                        'type': parts[0],
                        'tags': frozenset(parts[2:])
                    })
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    return paintings


def create_frameglasses(paintings):
    landscapes = []
    portraits = []
    
    for p in paintings:
        if p['type'] == 'L':
            landscapes.append({'ids': [p['id']], 'tags': p['tags']})
        else:
            portraits.append(p)
    
    for i in range(0, len(portraits) - 1, 2):
        p1, p2 = portraits[i], portraits[i + 1]
        landscapes.append({
            'ids': [p1['id'], p2['id']],
            'tags': p1['tags'] | p2['tags']
        })
    
    return landscapes


def calculate_score(tags1, tags2):
    common = len(tags1 & tags2)
    only_1 = len(tags1 - tags2)
    only_2 = len(tags2 - tags1)
    return min(common, only_1, only_2)


def calculate_global_score(ordered_frameglasses):
    if len(ordered_frameglasses) < 2:
        return 0
    return sum(
        calculate_score(ordered_frameglasses[i]['tags'], ordered_frameglasses[i + 1]['tags'])
        for i in range(len(ordered_frameglasses) - 1)
    )


def strategy_enhanced_cluster(frameglasses):
    if len(frameglasses) <= 1:
        return frameglasses[:]

    tag_frequency = Counter()
    for fg in frameglasses:
        tag_frequency.update(fg['tags'])

    def get_primary_tag(fg):
        if not fg['tags']:
            return ""
        sorted_tags = sorted(fg['tags'])
        return max(sorted_tags, key=lambda t: (tag_frequency[t], t))

    clusters = defaultdict(list)
    for fg in frameglasses:
        primary = get_primary_tag(fg)
        clusters[primary].append(fg)

    for tag in clusters:
        clusters[tag].sort(key=lambda fg: (tuple(sorted(fg['tags'])), tuple(fg['ids'])))

    cluster_keys = list(clusters.keys())
    if len(cluster_keys) <= 1:
        return sum(clusters.values(), [])

    cluster_keys.sort(key=lambda k: len(clusters[k]), reverse=True)
    
    used_clusters = set()
    result = []
    
    current_key = cluster_keys[0]
    result.extend(clusters[current_key])
    used_clusters.add(current_key)
    
    while len(used_clusters) < len(cluster_keys):
        last_tags = result[-1]['tags']
        
        best_score = -1
        best_key = None
        
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
        
        if best_key is None:
            for key in cluster_keys:
                if key not in used_clusters:
                    best_key = key
                    break
        
        result.extend(clusters[best_key])
        used_clusters.add(best_key)
    
    return result

def strategy_greedy_best_neighbor(frameglasses, seed=None):
    n = len(frameglasses)
    if n <= 1:
        return frameglasses[:]

    if seed is not None:
        random.seed(seed)
    else:
        random.seed(RANDOM_SEED)

    used = [False] * n
    result = []

    start_idx = random.randint(0, n - 1)
    result.append(frameglasses[start_idx])
    used[start_idx] = True

    for _ in range(n - 1):
        current = result[-1]
        current_tags = current['tags']
        best_score = -1
        best_idx = -1

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
    result = initial_order[:]
    n = len(result)
    
    if n < window_size:
        return result
    
    for start in range(0, n - window_size, window_size // 2):
        end = min(start + window_size, n)
        window = result[start:end]
        
        # Use multi-start greedy on window
        if len(window) < 5000:
            optimized_window = strategy_multiple_random_greedy(window, num_attempts=3)
        else:
            optimized_window = strategy_enhanced_cluster(window)
        
        # Check if improvement
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
        
        if new_score > old_score:
            result[start:end] = optimized_window
    
    return result



def strategy_2opt(initial_order, max_iterations=5, check_every=20):
    result = initial_order[:]
    n = len(result)
    
    if n < 4:
        return result
    
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        for i in range(0, n - 3, check_every):
            for j in range(i + 2, min(i + 50, n - 1)):
                score_before = 0
                if i > 0:
                    score_before += calculate_score(result[i-1]['tags'], result[i]['tags'])
                score_before += calculate_score(result[i]['tags'], result[i+1]['tags'])
                if j < n - 1:
                    score_before += calculate_score(result[j]['tags'], result[j+1]['tags'])
                if j > i + 1:
                    score_before += calculate_score(result[j-1]['tags'], result[j]['tags'])
                
                result[i], result[j] = result[j], result[i]
                
                score_after = 0
                if i > 0:
                    score_after += calculate_score(result[i-1]['tags'], result[i]['tags'])
                score_after += calculate_score(result[i]['tags'], result[i+1]['tags'])
                if j < n - 1:
                    score_after += calculate_score(result[j]['tags'], result[j+1]['tags'])
                if j > i + 1:
                    score_after += calculate_score(result[j-1]['tags'], result[j]['tags'])
                
                if score_after > score_before:
                    improved = True
                else:
                    result[i], result[j] = result[j], result[i]
    
    return result


def running_algorithm(frameglasses):
    """
    Score: 382,926 in 2.75 seconds
    
    Steps:
    1. Enhanced Cluster (smart grouping)
    2. Window Optimization (size=200)
    3. 2-Opt Enhancement (5 iterations)
    """
    print("   Step 1/3: Enhanced clustering...")
    result = strategy_enhanced_cluster(frameglasses)
    
    print("   Step 2/3: Window optimization...")
    result = strategy_window_optimization(result, window_size=200)
    
    print("   Step 3/3: 2-Opt enhancement...")
    result = strategy_2opt(result, max_iterations=5, check_every=20)
    
    return result


def write_output(filename, ordered_frameglasses):
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    
    with open(filename, 'w') as f:
        f.write(f"{len(ordered_frameglasses)}\n")
        for fg in ordered_frameglasses:
            f.write(" ".join(map(str, fg['ids'])) + "\n")


def main(input_file, output_file):
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
    

    print(f"Score: {score:,}")
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
        input_file = DEFAULT_INPUT_PATH
        output_file = './submission_11_randomizing_paintings.txt'

    main(input_file, output_file)