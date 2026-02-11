# -*- coding: utf-8 -*-
"""
Filename: HW1FinalSolution.py
Author: Donnel Garner
Date: 2/12/2026
Description: Breadth-First Search (BFS) and Depth-First Search (DFS) for the 24-puzzle.

Implements uninformed search for the 24-puzzle (5x5 sliding puzzle):
1) Breadth-First Search (BFS)
2) Depth-First Search (DFS) with a user-chosen depth limit

Input format:
- User enters 25 integers separated by commas (spaces allowed), e.g.:
  2,11,0,4,5,6,1,3,9,12,8,19,13,7,10,18,17,14,15,20,16,21,22,23,24

Conventions:
- 0 represents the blank tile.

Assignment note:
- DFS specifically prevents returning to a state already on the *current solution path*,
  matching "avoid returning to states that have already been visited on the current solution path".
"""

from collections import deque
import time
import tracemalloc
import sys


# ----------------------------
# Puzzle definitions & helpers
# ----------------------------

SIZE = 5  # 5x5 board
N_TILES = SIZE * SIZE  # 25
GOAL_STATE = tuple(range(1, N_TILES)) + (0,)


def print_board(state):
    """Pretty-print a 25-length tuple as a 5x5 grid."""
    for i in range(0, N_TILES, SIZE):
        row = state[i:i + SIZE]
        print(" ".join(f"{x:2}" if x != 0 else "  " for x in row))
    print()


def get_neighbors(state):
    """
    Generate all valid neighbor states by moving the BLANK (0).
    This follows the assignment hint to model moving the blank around.
    """
    neighbors = []

    zero_index = state.index(0)
    row = zero_index // SIZE
    col = zero_index % SIZE

    move_offsets = []
    if row > 0:
        move_offsets.append(-SIZE)  # up
    if row < SIZE - 1:
        move_offsets.append(SIZE)   # down
    if col > 0:
        move_offsets.append(-1)     # left
    if col < SIZE - 1:
        move_offsets.append(1)      # right

    for offset in move_offsets:
        new_index = zero_index + offset
        new_state = list(state)
        new_state[zero_index], new_state[new_index] = new_state[new_index], new_state[zero_index]
        neighbors.append(tuple(new_state))

    return neighbors


def inversion_count(state):
    """
    Count inversions in the permutation, ignoring the blank (0).
    Inversion = pair (i,j) such that i<j and state[i] > state[j], excluding 0.
    """
    arr = [x for x in state if x != 0]
    inv = 0
    # O(n^2) is fine for n=24
    for i in range(len(arr)):
        ai = arr[i]
        for j in range(i + 1, len(arr)):
            if ai > arr[j]:
                inv += 1
    return inv


def is_solvable_5x5(state):
    """
    Solvability test for odd grid width (5x5):
    - If grid width is odd, puzzle is solvable iff inversion count is even.
    """
    inv = inversion_count(state)
    return (inv % 2) == 0


def parse_state_from_csv(text):
    """
    Parse user input like:
      "2,11,0,4,5,...,24"
    Returns a tuple of 25 ints or raises ValueError.
    """
    parts = [p.strip() for p in text.strip().split(",") if p.strip() != ""]
    if len(parts) != N_TILES:
        raise ValueError(f"Expected {N_TILES} numbers, got {len(parts)}.")

    try:
        nums = [int(p) for p in parts]
    except ValueError:
        raise ValueError("All entries must be integers.")

    # Validate exact tile set 0..24, no duplicates
    required = set(range(N_TILES))
    got = set(nums)
    if got != required:
        missing = sorted(required - got)
        extra = sorted(got - required)
        msg = []
        if missing:
            msg.append(f"Missing: {missing}")
        if extra:
            msg.append(f"Unexpected: {extra}")
        # Also detect duplicates
        if len(nums) != len(set(nums)):
            msg.append("Duplicates detected.")
        raise ValueError("Invalid tile set. Must contain each of 0..24 exactly once. " + " ".join(msg))

    return tuple(nums)


def get_rss_bytes():
    """
    Best-effort RSS (resident set size) in bytes.
    Works on Unix/macOS via resource. Returns None if unavailable.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux: KB, macOS: bytes (heuristic)
        if usage < 10**9:
            return int(usage * 1024)
        return int(usage)
    except Exception:
        return None


def fmt_bytes(n):
    """Human-readable byte formatting."""
    if n is None:
        return "N/A"
    n = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ----------------------------
# BFS implementation
# ----------------------------

def bfs(start, node_limit=None, time_limit_sec=None):
    """
    Breadth-First Search.
    - Complete & optimal (shortest path) if it can finish.
    - Very high memory usage on large puzzles.

    Optional safety limits:
    - node_limit: stop after generating this many nodes
    - time_limit_sec: stop after this many seconds

    Returns: (solution_path_or_None, stats_dict)
    """
    stats = {
        "algorithm": "BFS",
        "expanded": 0,
        "generated": 0,
        "max_frontier": 0,
        "found": False,
        "solution_moves": None,
        "runtime_sec": None,
        "peak_py_bytes": None,
        "rss_bytes": None,
        "stopped_reason": None,
    }

    start_time = time.time()
    tracemalloc.start()

    queue = deque([start])

    # parent dict acts as visited + path reconstruction
    parent = {start: None}
    stats["generated"] = 1

    while queue:
        # safety: time limit
        if time_limit_sec is not None and (time.time() - start_time) > time_limit_sec:
            stats["stopped_reason"] = f"Time limit reached ({time_limit_sec} sec)"
            break

        stats["max_frontier"] = max(stats["max_frontier"], len(queue))
        state = queue.popleft()

        # goal test
        if state == GOAL_STATE:
            stats["found"] = True
            path = []
            cur = state
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()

            end_time = time.time()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            stats["solution_moves"] = len(path) - 1
            stats["runtime_sec"] = end_time - start_time
            stats["peak_py_bytes"] = peak
            stats["rss_bytes"] = get_rss_bytes()
            return path, stats

        stats["expanded"] += 1

        for neighbor in get_neighbors(state):
            if neighbor not in parent:
                parent[neighbor] = state
                queue.append(neighbor)
                stats["generated"] += 1

                # safety: node limit
                if node_limit is not None and stats["generated"] >= node_limit:
                    stats["stopped_reason"] = f"Node limit reached ({node_limit} generated)"
                    queue.clear()
                    break

    end_time = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stats["runtime_sec"] = end_time - start_time
    stats["peak_py_bytes"] = peak
    stats["rss_bytes"] = get_rss_bytes()
    return None, stats


# ----------------------------
# DFS implementation (depth-limited, path-only cycle avoidance)
# ----------------------------

def is_on_current_path(nodes, node_index, candidate_state):
    """
    Check whether candidate_state appears on the current root->node path.
    This enforces "no repeated states in a solution path".
    """
    i = node_index
    while i is not None:
        if nodes[i]["state"] == candidate_state:
            return True
        i = nodes[i]["parent"]
    return False


def dfs_depth_limited(start, depth_limit, node_limit=None, time_limit_sec=None):
    """
    Depth-Limited DFS.
    - Enforces: do not revisit states already on the current solution path.
    - Not optimal.
    - Often "hangs" without a depth limit; depth limit makes it measurable.

    Optional safety limits:
    - node_limit: stop after generating this many nodes
    - time_limit_sec: stop after this many seconds

    Returns: (solution_path_or_None, stats_dict)
    """
    stats = {
        "algorithm": "DFS (depth-limited)",
        "depth_limit": depth_limit,
        "expanded": 0,
        "generated": 0,
        "max_frontier": 0,
        "found": False,
        "solution_moves": None,
        "runtime_sec": None,
        "peak_py_bytes": None,
        "rss_bytes": None,
        "stopped_reason": None,
    }

    start_time = time.time()
    tracemalloc.start()

    # nodes store parent pointers for reconstruction + depth for the limit
    nodes = [{"state": start, "parent": None, "depth": 0}]
    stack = [0]
    stats["generated"] = 1

    while stack:
        # safety: time limit
        if time_limit_sec is not None and (time.time() - start_time) > time_limit_sec:
            stats["stopped_reason"] = f"Time limit reached ({time_limit_sec} sec)"
            break

        stats["max_frontier"] = max(stats["max_frontier"], len(stack))
        node_idx = stack.pop()
        node = nodes[node_idx]
        state = node["state"]
        depth = node["depth"]

        if state == GOAL_STATE:
            stats["found"] = True
            path = []
            i = node_idx
            while i is not None:
                path.append(nodes[i]["state"])
                i = nodes[i]["parent"]
            path.reverse()

            end_time = time.time()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            stats["solution_moves"] = len(path) - 1
            stats["runtime_sec"] = end_time - start_time
            stats["peak_py_bytes"] = peak
            stats["rss_bytes"] = get_rss_bytes()
            return path, stats

        # respect depth limit
        if depth >= depth_limit:
            continue

        stats["expanded"] += 1

        for neighbor in get_neighbors(state):
            # Only avoid repeats on the CURRENT path (matches assignment wording)
            if is_on_current_path(nodes, node_idx, neighbor):
                continue

            nodes.append({"state": neighbor, "parent": node_idx, "depth": depth + 1})
            stack.append(len(nodes) - 1)
            stats["generated"] += 1

            # safety: node limit
            if node_limit is not None and stats["generated"] >= node_limit:
                stats["stopped_reason"] = f"Node limit reached ({node_limit} generated)"
                stack.clear()
                break

    end_time = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stats["runtime_sec"] = end_time - start_time
    stats["peak_py_bytes"] = peak
    stats["rss_bytes"] = get_rss_bytes()
    return None, stats


# ----------------------------
# User interface / main
# ----------------------------

def print_stats(stats):
    print("\n=== Run Statistics ===")
    print(f"Algorithm: {stats.get('algorithm')}")
    if "depth_limit" in stats:
        print(f"Depth limit: {stats['depth_limit']}")
    print(f"Found solution: {stats['found']}")
    print(f"Expanded nodes: {stats['expanded']}")
    print(f"Generated nodes: {stats['generated']}")
    print(f"Max frontier size: {stats['max_frontier']}")
    print(f"Runtime: {stats['runtime_sec']:.4f} sec")
    print(f"Peak Python memory (tracemalloc): {fmt_bytes(stats['peak_py_bytes'])}")
    print(f"RSS (best effort): {fmt_bytes(stats['rss_bytes'])}")
    if stats.get("stopped_reason"):
        print(f"Stopped reason: {stats['stopped_reason']}")
    if stats.get("solution_moves") is not None:
        print(f"Solution moves: {stats['solution_moves']}")


def main():
    print("24-Puzzle Uninformed Search")
    print("----------------------------------------")
    print("Enter the puzzle as 25 comma-separated integers (0..24), where 0 is the blank.")
    print("Example:")
    print("  2,11,0,4,5,6,1,3,9,12,8,19,13,7,10,18,17,14,15,20,16,21,22,23,24\n")

    # Read puzzle input
    while True:
        try:
            raw = input("Puzzle input: ").strip()
            state = parse_state_from_csv(raw)
            break
        except ValueError as e:
            print(f"Input error: {e}\nTry again.\n")

    print("\nYour puzzle:")
    print_board(state)

    # Solvability check (useful so BFS/DFS don't run forever on impossible inputs)
    inv = inversion_count(state)
    solvable = is_solvable_5x5(state)
    print(f"Inversion count (ignoring blank): {inv}")
    print(f"Solvable on 5x5: {solvable}")
    if not solvable:
        print("\nThis configuration is NOT solvable on a 5x5 grid (odd width => inversions must be even).")
        print("Search would never find the goal. Exiting.")
        sys.exit(0)

    # Choose algorithm
    print("\nChoose search algorithm:")
    print("  1) BFS (shortest solution if it finishes, but may run out of memory)")
    print("  2) DFS (depth-limited; may find a solution within the limit, not guaranteed shortest)")
    choice = input("Enter 1 or 2: ").strip()

    # Safety limits (recommended so you always get stats back)
    # You can set these to None to remove limits, but be careful.
    DEFAULT_TIME_LIMIT = 20  # seconds
    DEFAULT_NODE_LIMIT = 300_000  # generated states

    print("\nSafety limits (recommended):")
    print(f"  Default time limit: {DEFAULT_TIME_LIMIT} seconds")
    print(f"  Default node limit: {DEFAULT_NODE_LIMIT} generated states")
    print("  Press Enter to accept defaults.\n")

    t_in = input("Time limit seconds (or blank): ").strip()
    n_in = input("Node limit generated (or blank): ").strip()

    time_limit = DEFAULT_TIME_LIMIT if t_in == "" else (None if t_in.lower() == "none" else float(t_in))
    node_limit = DEFAULT_NODE_LIMIT if n_in == "" else (None if n_in.lower() == "none" else int(n_in))

    if choice == "1":
        print("\nRunning BFS...\n")
        solution, stats = bfs(state, node_limit=node_limit, time_limit_sec=time_limit)

    elif choice == "2":
        # Ask for depth limit
        d_in = input("\nDFS depth limit (e.g., 30, 60, 100): ").strip()
        try:
            depth_limit = int(d_in)
            if depth_limit < 0:
                raise ValueError
        except ValueError:
            print("Invalid depth limit. Using 50.")
            depth_limit = 50

        print(f"\nRunning DFS with depth limit = {depth_limit}...\n")
        solution, stats = dfs_depth_limited(state, depth_limit=depth_limit,
                                            node_limit=node_limit, time_limit_sec=time_limit)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    print_stats(stats)

    if solution:
        print("\n=== Solution Path ===")
        print("NOTE: Printing the full path can be long if the solution is large.\n")
        for s in solution:
            print_board(s)
    else:
        print("\nNo solution found within the limits/constraints.")
        print("Tip: Increase the time limit / node limit, or (for DFS) increase the depth limit.")


if __name__ == "__main__":
    main()
