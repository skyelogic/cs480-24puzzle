<?php

function parseGrid(string $raw): array {
    // Accept whitespace-separated numbers, 25 total, 0 represents blank.
    $parts = preg_split('/\s+/', trim($raw));
    $parts = array_values(array_filter($parts, fn($x) => $x !== ''));

    if (count($parts) !== 25) {
        throw new InvalidArgumentException("Expected 25 numbers for a 5×5 grid, got " . count($parts) . ".");
    }

    $nums = array_map('intval', $parts);

    // Validate contains 0..24 exactly once
    $seen = [];
    foreach ($nums as $n) {
        if ($n < 0 || $n > 24) throw new InvalidArgumentException("All values must be between 0 and 24.");
        if (isset($seen[$n])) throw new InvalidArgumentException("Duplicate value detected: $n");
        $seen[$n] = true;
    }
    for ($i=0; $i<=24; $i++) {
        if (!isset($seen[$i])) throw new InvalidArgumentException("Missing value: $i");
    }

    return $nums;
}

function goalState25(): array {
    $g = range(1, 24);
    $g[] = 0;
    return $g;
}

function keyOf(array $state): string {
    // Fast enough for PHP; can optimize later if needed
    return implode(',', $state);
}

function findZeroIndex(array $state): int {
    $idx = array_search(0, $state, true);
    if ($idx === false) throw new RuntimeException("No blank (0) found in state.");
    return $idx;
}

function neighbors(array $state): array {
    // Returns list of [newState, moveChar]
    // moveChar describes blank movement: U/D/L/R (blank moved Up means swapped with tile above).
    $n = 5;
    $z = findZeroIndex($state);
    $r = intdiv($z, $n);
    $c = $z % $n;

    $out = [];

    // Up: swap with r-1,c
    if ($r > 0) {
        $s = $state;
        $swap = ($r-1)*$n + $c;
        [$s[$z], $s[$swap]] = [$s[$swap], $s[$z]];
        $out[] = [$s, 'U'];
    }
    // Down
    if ($r < $n-1) {
        $s = $state;
        $swap = ($r+1)*$n + $c;
        [$s[$z], $s[$swap]] = [$s[$swap], $s[$z]];
        $out[] = [$s, 'D'];
    }
    // Left
    if ($c > 0) {
        $s = $state;
        $swap = $r*$n + ($c-1);
        [$s[$z], $s[$swap]] = [$s[$swap], $s[$z]];
        $out[] = [$s, 'L'];
    }
    // Right
    if ($c < $n-1) {
        $s = $state;
        $swap = $r*$n + ($c+1);
        [$s[$z], $s[$swap]] = [$s[$swap], $s[$z]];
        $out[] = [$s, 'R'];
    }

    return $out;
}

function bfsSolve(array $start, array $goal, int $maxDepth = 50): array {
    $startKey = keyOf($start);
    $goalKey  = keyOf($goal);

    if ($startKey === $goalKey) {
        return [
            'status' => 'solved',
            'depth' => 0,
            'moves' => [],
            'expanded' => 0,
            'visited' => 1,
        ];
    }

    // BFS frontier
    $q = new SplQueue();

    // Parent pointers to reconstruct path:
    // parent[stateKey] = [parentKey, moveChar]
    $parent = [];
    $depth  = [];

    $parent[$startKey] = [null, null];
    $depth[$startKey] = 0;

    $q->enqueue($start);
    $visitedCount = 1;
    $expanded = 0;

    while (!$q->isEmpty()) {
        $cur = $q->dequeue();
        $curKey = keyOf($cur);
        $curDepth = $depth[$curKey];

        // Optional safety cutoff for web app
        if ($curDepth >= $maxDepth) {
            continue;
        }

        $expanded++;

        foreach (neighbors($cur) as [$next, $move]) {
            $nextKey = keyOf($next);

            // Graph-level visited check prevents repeats in any discovered path.
            if (isset($parent[$nextKey])) continue;

            $parent[$nextKey] = [$curKey, $move];
            $depth[$nextKey]  = $curDepth + 1;
            $visitedCount++;

            if ($nextKey === $goalKey) {
                $moves = reconstructMoves($parent, $goalKey);
                return [
                    'status' => 'solved',
                    'depth' => count($moves),
                    'moves' => $moves,
                    'expanded' => $expanded,
                    'visited' => $visitedCount,
                ];
            }

            $q->enqueue($next);
        }
    }

    return [
        'status' => 'cutoff_or_unsolved',
        'depth' => null,
        'moves' => [],
        'expanded' => $expanded,
        'visited' => $visitedCount,
    ];
}

function reconstructMoves(array $parent, string $goalKey): array {
    $moves = [];
    $k = $goalKey;
    while (true) {
        [$pk, $mv] = $parent[$k];
        if ($pk === null) break;
        $moves[] = $mv;
        $k = $pk;
    }
    return array_reverse($moves);
}
