<?php
require_once __DIR__ . '/bfs_solver.php';

$default = "9 24 3 5 17
6 0 13 19 10
11 21 22 1 20
16 4 14 12 15
8 18 23 2 7";

$result = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $raw = trim($_POST['grid'] ?? '');
    $maxDepth = (int)($_POST['maxDepth'] ?? 50);

    try {
        $start = parseGrid($raw);
        $goal  = goalState25(); // 1..24 then 0

        $t0 = microtime(true);
        $result = bfsSolve($start, $goal, $maxDepth);
        $t1 = microtime(true);

        $result['wall_seconds'] = $t1 - $t0;
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}
?>
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>24-Puzzle BFS Solver</title>
  <style>
    body{font-family:system-ui,Segoe UI,Arial;margin:24px;max-width:900px}
    textarea{width:420px;height:160px;font-family:ui-monospace,Consolas,monospace}
    .row{display:flex;gap:32px;align-items:flex-start}
    .card{padding:16px;border:1px solid #ddd;border-radius:10px}
    code{background:#f6f6f6;padding:2px 6px;border-radius:6px}
  </style>
</head>
<body>
  <h1>24-Puzzle BFS Solver</h1>

  <div class="row">
    <div class="card">
      <form method="post">
        <label>Enter 5×5 grid (use <code>0</code> for blank):</label><br>
        <textarea name="grid"><?= htmlspecialchars($_POST['grid'] ?? $default) ?></textarea><br><br>

        <label>Max depth cutoff (website safety):</label>
        <input type="number" name="maxDepth" value="<?= htmlspecialchars($_POST['maxDepth'] ?? 50) ?>" min="0" max="200"/>
        <button type="submit">Solve with BFS</button>
      </form>

      <p style="color:#666">
        Goal is <code>1..24</code> with <code>0</code> at the end.
      </p>
    </div>

    <div class="card" style="flex:1">
      <h2>Result</h2>
      <?php if ($error): ?>
        <p style="color:#b00"><?= htmlspecialchars($error) ?></p>
      <?php elseif ($result): ?>
        <?php if ($result['status'] === 'solved'): ?>
          <p><b>Solved!</b></p>
          <p>Moves: <b><?= (int)$result['depth'] ?></b></p>
          <p>Expanded nodes: <b><?= (int)$result['expanded'] ?></b></p>
          <p>Visited states: <b><?= (int)$result['visited'] ?></b></p>
          <p>Wall time: <b><?= number_format($result['wall_seconds'], 4) ?>s</b></p>

          <h3>Move sequence</h3>
          <pre><?= htmlspecialchars(implode(' ', $result['moves'])) ?></pre>
        <?php else: ?>
          <p><b>No solution found within depth cutoff.</b></p>
          <p>Expanded nodes: <b><?= (int)$result['expanded'] ?></b></p>
          <p>Visited states: <b><?= (int)$result['visited'] ?></b></p>
          <p>Wall time: <b><?= number_format($result['wall_seconds'], 4) ?>s</b></p>
          <p style="color:#666">Try increasing max depth (careful: BFS grows fast).</p>
        <?php endif; ?>
      <?php else: ?>
        <p style="color:#666">Submit a grid to run BFS.</p>
      <?php endif; ?>
    </div>
  </div>
</body>
</html>
