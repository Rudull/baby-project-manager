# Scratch tests

Run from project root (conda env `baby`):

```sh
conda activate baby
python scratch/unit/test_simple.py
python scratch/integration/test_commands.py
python scratch/e2e/test_auto.py
python scratch/e2e/test_manual.py
```

Suites:

- **unit/** — isolated command-system logic against a mocked window (no real `MainWindow`, fastest).
- **integration/** — the same command-system operations (add/delete/move/duplicate/subtask/color/undo/redo) against a real `MainWindow`, with assertions and a pass/fail summary.
- **e2e/** — the full app with a real window: `test_auto.py` drives it automatically end-to-end and exits on its own; `test_manual.py` opens the app with sample tasks and an on-screen instructions dialog for a human to click through (Ctrl+Z/Ctrl+Y), closing itself after 2 minutes.

`debug_commands.py` (at the `scratch/` root) is an interactive CLI menu for manually poking at individual commands one at a time — a dev tool, not an automated test.

`tareas de test.bpm` is a sample project file for manually opening via File > Open during exploratory testing.
