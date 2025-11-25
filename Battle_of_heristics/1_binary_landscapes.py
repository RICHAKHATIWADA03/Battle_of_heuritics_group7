import random
import time
import sys
import os

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

class Painting:
    __slots__ = ['id', 'orientation', 'num_of_tags', 'tags']

    def __init__(self, pid, orientation, num_of_tags, tags):
        self.id = pid
        self.orientation = orientation
        self.num_of_tags = num_of_tags
        self.tags = tags


def parse_input_file(file_path):
    paintings = []
    with open(file_path, 'r') as file:
        n = int(file.readline())
        for i in range(n):
            parts = file.readline().strip().split()
            orientation = parts[0]
            num_tags = int(parts[1])
            tags = parts[2:]
            painting = Painting(i, orientation, num_tags, tags)
            paintings.append(painting)
    return paintings


def create_frameglasses(paintings):
    frameglasses_landscapes = []
    for painting in paintings:
        frameglasses_landscapes.append({
            'ids': [painting.id],
            'number_of_tags': painting.num_of_tags,
            'tags': set(painting.tags)
        })
    return frameglasses_landscapes


def tag_frequency_index(frameglasses):
    index = {}
    for idx, frame in enumerate(frameglasses):
        for tag in frame['tags']:
            if tag not in index:
                index[tag] = set()
            index[tag].add(idx)
    return index


def tag_global_frequency(frameglasses):
    freq = {}
    for frame in frameglasses:
        for tag in frame['tags']:
            freq[tag] = freq.get(tag, 0) + 1
    return freq


def smart_ordering(frameglasses):
    # Reset random seed for consistent results
    random.seed(RANDOM_SEED)
    
    ordered = []
    remaining = set(range(len(frameglasses)))
    index = tag_frequency_index(frameglasses)
    tag_freq = tag_global_frequency(frameglasses)

    # Start with deterministic choice instead of random
    current_idx = max(remaining, key=lambda i: len(frameglasses[i]['tags']))
    remaining.remove(current_idx)
    ordered.append(frameglasses[current_idx])

    while remaining:
        current_tags = ordered[-1]['tags']
        candidates = set()
        for tag in current_tags:
            candidates |= index.get(tag, set())
        candidates &= remaining

        if not candidates:
            # Pick deterministically instead of random
            next_idx = min(remaining)
            remaining.remove(next_idx)
        else:
            best_score = -1
            best_idx = None
            best_freq = float('inf')

            sample_size = min(500, len(candidates))
            # Sort candidates for deterministic sampling
            sampled = random.sample(sorted(list(candidates)), sample_size)
            
            for idx in sampled:
                next_tags = frameglasses[idx]['tags']
                common = len(current_tags & next_tags)
                unique_cur = len(current_tags - next_tags)
                unique_nxt = len(next_tags - current_tags)
                score = min(common, unique_cur, unique_nxt)

                # Tie-breaker: prefer frames with less common tags (for diversity)
                freq_penalty = sum(tag_freq[t] for t in next_tags)
                if score > best_score or (score == best_score and freq_penalty < best_freq):
                    best_score = score
                    best_idx = idx
                    best_freq = freq_penalty

            next_idx = best_idx
            remaining.remove(next_idx)

        ordered.append(frameglasses[next_idx])

    return ordered


def calculate_satisfaction_score(frameglasses):
    if len(frameglasses) < 2:
        return 0

    total_score = 0
    for i in range(len(frameglasses) - 1):
        current = frameglasses[i]['tags']
        next_frame = frameglasses[i + 1]['tags']
        common_tags = len(current & next_frame)
        unique_current = len(current - next_frame)
        unique_next = len(next_frame - current)
        local_score = min(common_tags, unique_current, unique_next)
        total_score += local_score

    return total_score


def write_output_file(frameglasses, output_path):
    """Write output file in correct format."""
    dirname = os.path.dirname(output_path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    
    with open(output_path, 'w') as file:
        file.write(f"{len(frameglasses)}\n")
        for frame in frameglasses:
            file.write(" ".join(map(str, frame['ids'])) + "\n")


def main(input_file, output_file):
    print(f"Reading: {input_file}")
    start_time = time.time()
    
    paintings = parse_input_file(input_file)
    print(f"Loaded {len(paintings):,} paintings")
    
    print("Creating frameglasses...")
    frame_glasses_landscapes = create_frameglasses(paintings)
    print(f"Created {len(frame_glasses_landscapes):,} frameglasses")
    
    print("Ordering frameglasses...")
    ordered_frames = smart_ordering(frame_glasses_landscapes)
    
    score = calculate_satisfaction_score(ordered_frames)
    elapsed = time.time() - start_time
    
    print(f"\nScore: {score:,}")
    print(f"Time taken: {elapsed:.2f} seconds")
    
    print(f"\nWriting: {output_file}")
    write_output_file(ordered_frames, output_file)
    print("Done!")
    
    return score


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = './Data/1_binary_landscapes.txt'
        output_file = './submission_1_binary_landscapes.txt'

    main(input_file, output_file)