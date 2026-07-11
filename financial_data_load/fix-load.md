# Plan: Reorganize and Clean Up `financial_data_load/`

Fixes the organizational drift identified in the review. The `src/` package is well-structured and stays as-is. Work is ordered from low-risk/high-value to larger refactors so each step can ship independently.

## Guiding decisions

- **README is the intent, code is the truth.** Where they disagree, update the README to match what the code actually does, unless the code is clearly a leftover (then remove the code).
- Preserve the `src/` module split, the intentional `lib/` copy, and the gitignored `backups/`/`logs/`/`plans/` dirs.
- Each numbered section is a self-contained change with its own verification.

---

## 1. Stop tracking snapshot artifacts (low risk, high value)

**Problem:** `snapshots/` holds 6 JSON files at 2.3 to 2.8 MB each. Four are committed to git even though the README says snapshots are git-ignored.

**Steps:**
1. Add `snapshots/` to the repo `.gitignore` (keep the directory with a `.gitkeep` so tooling that writes there still finds it).
2. `git rm --cached financial_data_load/snapshots/*.json` to untrack the four committed files without deleting them from disk.
3. Confirm the README statement that snapshots are git-ignored is now accurate.

**Verify:** `git ls-files financial_data_load/snapshots` returns nothing; `git check-ignore financial_data_load/snapshots` matches.

---

## 2. Fix README drift (low risk, high value)

**Problem:** The "File Structure" and command tables no longer match the code.

**Steps:**
1. Add `src/model_compare.py` to the documented file structure with a one-line description.
2. Reconcile the solutions table numbering with the actual file prefixes in `solution_srcs/` (`01_`, `03_`, `04_`, `05_`, `06_`). Either renumber the table to match the files or renumber the files to match the table. Decide as part of section 4.
3. Add the missing `main.py` commands to the "All Commands" table: `normalize`, `fix-companies`, `export-model`, `compare-models`. If any are dead (see section 6), remove them from the code instead of documenting them.
4. Correct the snapshot statement (covered by section 1).
5. Document `run_all_configs.sh` and `run_cleanse.sh`, or mark them as experiment-only dev scripts.

**Verify:** Every path and command in the README maps to a real file or subparser, and every subparser and tracked script appears in the README.

---

## 3. Document the `.env` variants (low risk)

**Problem:** Four env files sit at root (`.env`, `.env.final`, `.env.gold`, `.env.sample`) with no explanation of their roles.

**Steps:**
1. Add a short "Env files" subsection to the README: `.env` is the active config, `.env.sample` is the template, `.env.gold` and `.env.final` are fixtures consumed by `test_solutions.sh`.
2. Confirm `.env.gold` and `.env.final` stay untracked and are covered by `.gitignore`.

**Verify:** README explains each file; `git ls-files` shows only `.env.sample` tracked.

---

## 4. Reorganize `solution_srcs/` (medium risk)

**Problem:** One flat directory mixes real workshop solutions (small), large test harnesses (`01_test_full_data_load.py` at 31 KB, `04_00_test_all_sample_queries.py` at 28 KB), and shared helpers (`config.py`, `test_connection.py`).

**Steps:**
1. Split into two directories:
   - `solutions/` for the actual workshop solution scripts.
   - `tests/` for `01_test_full_data_load.py`, `01_01_test_lab1_csv_load.py`, `04_00_test_all_sample_queries.py`, `test_connection.py`.
2. Keep shared `config.py` where both can import it, or promote it to a location both can reach.
3. Settle the numbering scheme so file prefixes match the README solutions table (ties into section 2).
4. Update imports, `__init__.py` files, and the solution-loading logic in `main.py` (`_run_solution`, `_print_solutions_menu`) to the new paths.
5. Update `test_solutions.sh` for any moved test paths.

**Verify:** `uv run python main.py solutions` menu still lists and runs each solution; `./test_solutions.sh .env.gold` still discovers the tests.

---

## 5. Thin out `main.py` (medium risk)

**Problem:** `main.py` is 781 lines holding logging setup, 20+ `cmd_*` handlers, and all argparse registration.

**Steps:**
1. Create `src/commands/` and move the `cmd_*` handlers into cohesive modules (for example `data.py` for load/backup/restore, `cleanse.py` for cleanse/apply-cleanse/normalize/finalize, `resolution.py` for snapshot/resolve/compare/apply-merges/model compare, `misc.py` for test/verify/clean/samples/solutions).
2. Keep `_setup_logging` and `_fmt_elapsed` in a small shared helper module.
3. Leave `main()` as a thin argparse wiring layer that imports handlers and registers subparsers.
4. Preserve every existing command name and flag so the CLI surface does not change.

**Verify:** `uv run python main.py --help` lists the same commands; spot-check `test`, `verify`, and `samples` run unchanged.

---

## 6. Resolve loose root scripts and dead commands (medium risk, needs confirmation)

**Problem:** `verify_queries.py` (215 lines) duplicates the intent of `main.py verify` and is undocumented. `fix-companies` reads like a one-off patch command. `run_all_configs.sh` and `run_cleanse.sh` are tracked but undocumented.

**Steps:**
1. Decide `verify_queries.py`: fold its checks into `main.py verify` / `src/`, or document it as a standalone tool. If redundant, remove it.
2. Decide `fix-companies`: confirm whether it is still needed. If it was a one-off migration, remove the command and its handler; otherwise document it.
3. Decide the two shell scripts: keep and document as experiment runners, or move under a `scripts/` dir, or remove if obsolete.

**Confirm with the user before deleting anything in this section**, since these may still be used in workshop prep.

**Verify:** No dangling references in the README or `main.py` to removed items; retained items are documented.

---

## Suggested execution order

1. Sections 1, 2, 3 together (docs and gitignore, no behavior change).
2. Section 4 (solution_srcs reorg).
3. Section 5 (main.py refactor).
4. Section 6 (cleanup, after confirming with the user).

Ship and verify each block before starting the next.
