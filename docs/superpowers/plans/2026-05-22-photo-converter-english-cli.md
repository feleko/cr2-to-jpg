# Photo Converter — English CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the existing Polish CR2→JPG converter into a fully-English script with an interactive CLI plus argparse fallback, parallel conversion across CPU cores, and README + dependency manifests.

**Architecture:** Single-file `main.py` that dispatches between interactive prompts (no args) and argparse mode (with args). Small focused helper functions for prompting, file discovery, conversion, and the rich-based output. Conversion runs in a `ProcessPoolExecutor` (default workers = `os.cpu_count()`) so all cores are used. Two dependency manifests (`requirements.txt`, `pyproject.toml`) describe the same three runtime deps.

**Tech Stack:** Python 3.9+, `rawpy` (CR2 decoding), `imageio` (JPG encoding), `rich` (progress bar, colored output, summary table), stdlib `concurrent.futures` (parallelism).

---

## Notes for the implementer

- **No git repository.** Skip git/commit steps. There is no `.git` directory under `/Users/wonf/code/radagast/photo_converter/`.
- **No automated tests.** The spec explicitly opts out of a test suite for this iteration. Verification is manual via `example/13.CR2`.
- **Existing code:** `main.py` currently exists in Polish. It is replaced wholesale, not edited in place — the cleanest approach is to overwrite it with the new content in Task 2 and refine in subsequent tasks.
- **Working directory:** `/Users/wonf/code/radagast/photo_converter`.

---

## File Structure

| File | Status | Responsibility |
|------|--------|----------------|
| `requirements.txt` | create | Pinned dep list for `pip install -r` |
| `pyproject.toml` | create | Same deps in modern format |
| `main.py` | replace | The entire CLI: imports, helpers, prompts, conversion loop, entry point |
| `README.md` | create | macOS + Windows install/usage docs |
| `example/13.CR2` | unchanged | Sample input for verification |

`main.py` stays a single file. The internal structure groups related helpers (prompts together, conversion together, entry routing at the bottom). Keeping it one file is deliberate: the end user is a beginner who should be able to read the whole script top-to-bottom.

---

## Task 1: Dependency manifests

**Files:**
- Create: `/Users/wonf/code/radagast/photo_converter/requirements.txt`
- Create: `/Users/wonf/code/radagast/photo_converter/pyproject.toml`

- [ ] **Step 1: Write `requirements.txt`**

Path: `/Users/wonf/code/radagast/photo_converter/requirements.txt`

```
rawpy>=0.18
imageio>=2.0
rich>=13.0
```

- [ ] **Step 2: Write `pyproject.toml`**

Path: `/Users/wonf/code/radagast/photo_converter/pyproject.toml`

```toml
[project]
name = "photo-converter"
version = "0.1.0"
description = "Batch-convert Canon CR2 RAW photos to JPG."
requires-python = ">=3.9"
dependencies = [
    "rawpy>=0.18",
    "imageio>=2.0",
    "rich>=13.0",
]

[project.scripts]
photo-converter = "main:main"
```

No `[build-system]` block is added — the project is run as a script, not built as a package. The `[project.scripts]` entry is informational; users will run `python main.py` directly per the README.

- [ ] **Step 3: Verify files exist**

Run: `ls /Users/wonf/code/radagast/photo_converter/requirements.txt /Users/wonf/code/radagast/photo_converter/pyproject.toml`
Expected: both paths print, no errors.

---

## Task 2: Rewrite `main.py` — imports, console, convert_file

This task replaces the existing Polish `main.py` with the new English skeleton: imports (with friendly ImportError handling), a module-level `rich.Console`, and the `convert_file` function. Subsequent tasks add the rest.

**Files:**
- Replace: `/Users/wonf/code/radagast/photo_converter/main.py`

- [ ] **Step 1: Overwrite `main.py` with the skeleton below**

```python
#!/usr/bin/env python3
"""Convert Canon CR2 RAW photos to JPG, in batch.

Run with no arguments for the interactive prompts, or pass a folder
on the command line. See README.md for details.

One-time setup:
    pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

try:
    import rawpy
    import imageio.v2 as imageio
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
except ImportError:
    print("Missing libraries. Install them with:")
    print("    pip install -r requirements.txt")
    sys.exit(1)


console = Console()


def convert_file(source: Path, target: Path, quality: int) -> None:
    """Convert a single CR2 file to JPG using the camera's white balance."""
    with rawpy.imread(str(source)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=False,
            output_bps=8,
            highlight_mode=rawpy.HighlightMode.Blend,
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(str(target), rgb, quality=quality)


def main() -> None:
    raise NotImplementedError("Implemented in Task 5")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify imports load cleanly**

Run: `cd /Users/wonf/code/radagast/photo_converter && python -c "import main; print('ok')"`
Expected: prints `ok`. If it prints the "Missing libraries" hint, install deps first: `pip install -r requirements.txt`.

---

## Task 3: File discovery + conversion loop with rich output

Add the `find_cr2_files`, `run_conversion`, and `print_summary` helpers to `main.py`. These contain the core loop and the rich UI.

**Files:**
- Modify: `/Users/wonf/code/radagast/photo_converter/main.py` (insert helpers between `convert_file` and `main`)

- [ ] **Step 1: Add `find_cr2_files` immediately after `convert_file`**

```python
def find_cr2_files(folder: Path, recursive: bool) -> list[Path]:
    """Return CR2 files in `folder`, sorted, case-insensitive on extension."""
    pattern = "**/*" if recursive else "*"
    return sorted(
        p for p in folder.glob(pattern)
        if p.is_file() and p.suffix.lower() == ".cr2"
    )
```

- [ ] **Step 2: Add `print_summary` after `find_cr2_files`**

```python
def print_summary(converted: int, skipped: int, errors: int, elapsed: float) -> None:
    """Print a rich table summarizing the run."""
    table = Table(title="Done", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Converted", f"[green]{converted}[/green]")
    table.add_row("Skipped", f"[yellow]{skipped}[/yellow]")
    table.add_row("Errors", f"[red]{errors}[/red]")
    table.add_row("Elapsed", f"{elapsed:.0f}s")
    console.print()
    console.print(table)
```

- [ ] **Step 3: Add `run_conversion` after `print_summary`**

This version pre-filters skip-targets synchronously (so the `⊘` lines stay grouped at the top of the log), then submits the real work to a `ProcessPoolExecutor`. `convert_file` from Task 2 is at module scope and pickleable, so it can be the worker target directly.

```python
def run_conversion(
    input_folder: Path,
    output_folder: Path,
    quality: int,
    recursive: bool,
    overwrite: bool,
    workers: int | None = None,
) -> None:
    """Find CR2 files under `input_folder` and convert each to JPG in parallel."""
    files = find_cr2_files(input_folder, recursive)

    if not files:
        console.print(f"[yellow]No CR2 files found in '{input_folder}'.[/yellow]")
        return

    # Pre-filter: separate jobs from skip-targets so skip lines stay grouped.
    jobs: list[tuple[Path, Path]] = []
    skipped = 0
    for source in files:
        relative = source.relative_to(input_folder)
        target = (output_folder / relative).with_suffix(".jpg")
        if target.exists() and not overwrite:
            console.print(f"[yellow]⊘[/yellow] {source.name} (already exists)")
            skipped += 1
        else:
            jobs.append((source, target))

    worker_count = workers if workers and workers > 0 else (os.cpu_count() or 2)
    console.print(
        f"Found [bold]{len(files)}[/bold] CR2 file(s); "
        f"converting [bold]{len(jobs)}[/bold] using "
        f"[bold]{worker_count}[/bold] worker(s).\n"
    )

    converted = errors = 0
    start = time.time()

    if jobs:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
        )
        with progress, ProcessPoolExecutor(max_workers=worker_count) as pool:
            task_id = progress.add_task("Converting", total=len(jobs))
            futures = {
                pool.submit(convert_file, src, tgt, quality): (src, tgt)
                for src, tgt in jobs
            }
            for future in as_completed(futures):
                src, tgt = futures[future]
                try:
                    future.result()
                    console.print(f"[green]✓[/green] {src.name} → {tgt.name}")
                    converted += 1
                except Exception as e:
                    console.print(f"[red]✗[/red] {src.name}: {e}")
                    errors += 1
                progress.advance(task_id)

    elapsed = time.time() - start
    print_summary(converted, skipped, errors, elapsed)
```

Note on multiprocessing: on macOS Python uses the "spawn" start method, so each worker re-imports `main.py`. The `if __name__ == "__main__":` guard at the bottom of the file (already there from Task 2) is what prevents the workers from re-running `main()` on import. Do not remove it.

- [ ] **Step 4: Verify the module still imports**

Run: `cd /Users/wonf/code/radagast/photo_converter && python -c "import main; print('ok')"`
Expected: prints `ok`.

---

## Task 4: Interactive prompt helpers

Add four small helpers that ask the user for each input with sensible defaults and validation.

**Files:**
- Modify: `/Users/wonf/code/radagast/photo_converter/main.py` (insert before `main()`)

- [ ] **Step 1: Add `prompt_input_folder` after `run_conversion`**

```python
def prompt_input_folder() -> Path:
    """Ask for the input folder; re-prompt until the path is a real directory."""
    while True:
        raw = input("Folder with CR2 files: ").strip().strip('"').strip("'")
        if not raw:
            console.print("[red]Please enter a path.[/red]")
            continue
        path = Path(raw).expanduser()
        if not path.is_dir():
            console.print(f"[red]'{path}' is not a folder. Try again.[/red]")
            continue
        return path
```

The `.strip('"').strip("'")` handles users pasting a path quoted by the OS (common when dragging from Finder/Explorer).

- [ ] **Step 2: Add `prompt_output_folder` after `prompt_input_folder`**

```python
def prompt_output_folder(default: Path) -> Path:
    """Ask for the output folder; empty input falls back to `default`."""
    raw = input(
        f"Output folder (press Enter to use '{default}'): "
    ).strip().strip('"').strip("'")
    if not raw:
        return default
    return Path(raw).expanduser()
```

- [ ] **Step 3: Add `prompt_quality` after `prompt_output_folder`**

```python
def prompt_quality() -> int:
    """Ask for JPG quality 1-100; empty input → 92."""
    while True:
        raw = input("JPG quality 1-100 [92]: ").strip()
        if not raw:
            return 92
        try:
            value = int(raw)
        except ValueError:
            console.print("[red]Please enter a whole number.[/red]")
            continue
        if not 1 <= value <= 100:
            console.print("[red]Quality must be between 1 and 100.[/red]")
            continue
        return value
```

- [ ] **Step 4: Add `prompt_recursive` after `prompt_quality`**

```python
def prompt_recursive() -> bool:
    """Ask whether to descend into subfolders; default no."""
    while True:
        raw = input("Include subfolders? [y/N]: ").strip().lower()
        if raw in ("", "n", "no"):
            return False
        if raw in ("y", "yes"):
            return True
        console.print("[red]Please answer y or n.[/red]")
```

- [ ] **Step 5: Verify import still works**

Run: `cd /Users/wonf/code/radagast/photo_converter && python -c "import main; print('ok')"`
Expected: prints `ok`.

---

## Task 5: Mode dispatch — `run_interactive`, `run_with_args`, `main`

Replace the stub `main()` from Task 2 with real routing logic, and add the two mode entry points.

**Files:**
- Modify: `/Users/wonf/code/radagast/photo_converter/main.py` (replace the `main()` stub at the bottom)

- [ ] **Step 1: Add `run_interactive` immediately before the `main()` stub**

```python
def run_interactive() -> None:
    """Prompt the user for inputs and run the conversion."""
    console.print("[bold]CR2 → JPG converter[/bold]\n")
    input_folder = prompt_input_folder()
    output_folder = prompt_output_folder(input_folder)
    quality = prompt_quality()
    recursive = prompt_recursive()
    console.print()
    run_conversion(
        input_folder=input_folder,
        output_folder=output_folder,
        quality=quality,
        recursive=recursive,
        overwrite=False,
        workers=None,  # auto: all CPU cores
    )
```

- [ ] **Step 2: Add `run_with_args` immediately after `run_interactive`**

```python
def run_with_args(argv: list[str]) -> None:
    """Parse command-line arguments and run the conversion."""
    parser = argparse.ArgumentParser(
        description="Batch-convert Canon CR2 RAW photos to JPG.",
    )
    parser.add_argument("input_folder", help="Folder containing CR2 files")
    parser.add_argument(
        "output_folder",
        nargs="?",
        default=None,
        help="Folder for JPG output (default: same as input)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=92,
        help="JPG quality 1-100 (default: 92)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subfolders as well",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing JPG files (default: skip them)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: number of CPU cores)",
    )
    args = parser.parse_args(argv)

    input_folder = Path(args.input_folder).expanduser()
    if not input_folder.is_dir():
        console.print(
            f"[red]Error: folder '{input_folder}' does not exist.[/red]"
        )
        sys.exit(1)

    output_folder = (
        Path(args.output_folder).expanduser()
        if args.output_folder
        else input_folder
    )

    run_conversion(
        input_folder=input_folder,
        output_folder=output_folder,
        quality=args.quality,
        recursive=args.recursive,
        overwrite=args.overwrite,
        workers=args.workers,
    )
```

- [ ] **Step 3: Replace the `main()` stub with real dispatch**

Replace the existing two-line `main()` (`raise NotImplementedError(...)`) with:

```python
def main() -> None:
    if len(sys.argv) > 1:
        run_with_args(sys.argv[1:])
    else:
        run_interactive()
```

- [ ] **Step 4: Verify argparse help renders**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py --help`
Expected: usage line plus the five flags/positionals, exit 0.

---

## Task 6: Manual verification with `example/13.CR2`

This task confirms the actual conversion still works end-to-end after the rewrite. Requires `pip install -r requirements.txt` to have been run.

**Files:**
- Read-only: `/Users/wonf/code/radagast/photo_converter/example/13.CR2`

- [ ] **Step 1: Ensure deps are installed**

Run: `cd /Users/wonf/code/radagast/photo_converter && pip install -r requirements.txt`
Expected: pip reports `rawpy`, `imageio`, `rich` installed (or already-satisfied).

- [ ] **Step 2: Argparse-mode dry run on the sample**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py example`
Expected output:
- A "Found 1 CR2 file(s)" line.
- A green `✓ 13.CR2 → 13.jpg` line.
- A rich progress bar visible during the run.
- A summary table showing Converted=1, Skipped=0, Errors=0, Elapsed=<n>s.
- File `example/13.jpg` now exists.

Run: `ls /Users/wonf/code/radagast/photo_converter/example/`
Expected: both `13.CR2` and `13.jpg` listed.

- [ ] **Step 3: Confirm skip-existing behavior**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py example`
Expected: yellow `⊘ 13.CR2 (already exists)` and summary Skipped=1.

- [ ] **Step 4: Confirm overwrite + --workers flags work**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py example --overwrite --quality 85 --workers 2`
Expected: green `✓ 13.CR2 → 13.jpg`, Converted=1, the announcement line shows `using 2 worker(s)`. The `13.jpg` file's mtime should have changed.

- [ ] **Step 5: Argparse error path**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py does_not_exist`
Expected: red `Error: folder 'does_not_exist' does not exist.`, exit code 1. Check with `echo $?` immediately after — expect `1`.

- [ ] **Step 6: Spot-check interactive mode**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py`
At each prompt, type:
- `example` → Enter
- (Enter, accept default output folder)
- (Enter, accept default quality 92)
- (Enter, no recursion)

Expected: same output shape as argparse run — green `✓` line, summary table. Press Ctrl-C if you want to bail at any prompt; verify the script exits cleanly.

- [ ] **Step 7: Clean up generated JPG before finishing**

Run: `rm /Users/wonf/code/radagast/photo_converter/example/13.jpg`
Expected: file removed; `example/` contains only `13.CR2` again.

---

## Task 7: Write README.md

**Files:**
- Create: `/Users/wonf/code/radagast/photo_converter/README.md`

- [ ] **Step 1: Write the README**

Path: `/Users/wonf/code/radagast/photo_converter/README.md`

````markdown
# Photo Converter

Batch-convert Canon **CR2** RAW photos to **JPG**. Comes with an interactive prompt — just run it and answer the questions.

## What it does

Given a folder of `.CR2` files, it produces a `.jpg` for each one using the camera's white balance and a gentle highlight recovery. By default it skips files that already have a `.jpg` next to them, so you can re-run it safely. Conversion runs in parallel across all CPU cores, so a batch of a few hundred photos finishes in a fraction of the single-threaded time.

## Install — macOS

1. Open **Terminal** (Applications → Utilities → Terminal).
2. Check Python is installed:

   ```bash
   python3 --version
   ```

   If it prints something like `Python 3.11.x`, you're good. If not, install it from <https://www.python.org/downloads/macos/>.

3. `cd` into this folder. If the project lives on your Desktop:

   ```bash
   cd ~/Desktop/photo_converter
   ```

4. Create and activate a virtual environment (one-time):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

Next time you want to use it, just open Terminal, `cd` into the folder, and run `source .venv/bin/activate` before `python main.py`.

## Install — Windows

1. Install **Python 3.11+** from <https://www.python.org/downloads/windows/>.
   **Important:** on the first installer screen, tick **"Add python.exe to PATH"**.
2. Open **PowerShell** (Start menu → type "PowerShell").
3. `cd` into this folder. If the project lives in your Documents:

   ```powershell
   cd $HOME\Documents\photo_converter
   ```

4. Create and activate a virtual environment (one-time):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell complains about "running scripts is disabled", run this once and try again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

5. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

## How to use

### The easy way (interactive)

Just run:

```bash
python main.py
```

It will ask you:

1. **Folder with CR2 files** — drag the folder onto the Terminal/PowerShell window to paste its path, then press Enter.
2. **Output folder** — press Enter to put the JPGs alongside the originals, or paste a different folder.
3. **JPG quality** — press Enter for 92 (good default), or type a number 1–100.
4. **Include subfolders?** — `y` to recurse, Enter (or `n`) to keep it flat.

You'll see a progress bar and a summary at the end.

### The fast way (arguments)

If you prefer to type everything at once:

```bash
python main.py path/to/cr2s path/to/output --quality 85 --recursive
```

Available flags:

- `--quality N` — JPG quality 1–100, default 92.
- `--recursive` — also search subfolders.
- `--overwrite` — overwrite existing JPGs (otherwise they're skipped).
- `--workers N` — number of parallel workers (default: all CPU cores). Use a smaller number if the computer becomes too sluggish to use while converting.

Run `python main.py --help` to see this again.

## Troubleshooting

**`command not found: python`** (macOS)
Use `python3` instead of `python`.

**`pip` complains about installing `rawpy` on Apple Silicon (M1/M2/M3)**
Upgrade pip first, then retry:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**PowerShell says it can't run `Activate.ps1`** (Windows)
Run this once, then re-activate the venv:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**"Missing libraries" message when starting the script**
The virtual environment isn't activated. Run:
- macOS: `source .venv/bin/activate`
- Windows: `.\.venv\Scripts\Activate.ps1`

…then try again.
````

- [ ] **Step 2: Verify the file exists**

Run: `ls /Users/wonf/code/radagast/photo_converter/README.md`
Expected: path prints.

---

## Final verification

- [ ] **Step 1: Tree-check the final layout**

Run: `cd /Users/wonf/code/radagast/photo_converter && ls -la`
Expected to see at minimum: `main.py`, `requirements.txt`, `pyproject.toml`, `README.md`, `example/`, `docs/`.

- [ ] **Step 2: Confirm `main.py` has no Polish strings left**

Run: `cd /Users/wonf/code/radagast/photo_converter && grep -nE '[ąćęłńóśźż]|Błąd|jakosc|rekursywnie|nadpisuj|folder_wejsciowy|folder_wyjsciowy|konwertuj|pliki' main.py || echo "clean"`
Expected: prints `clean`.

- [ ] **Step 3: Quick smoke test**

Run: `cd /Users/wonf/code/radagast/photo_converter && python main.py example && rm -f example/13.jpg`
Expected: one converted file, summary table, then cleanup leaves only `example/13.CR2`.
