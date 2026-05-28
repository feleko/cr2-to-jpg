# Photo Converter — English CLI redesign

**Date:** 2026-05-22
**Status:** Approved

## Goal

Rewrite the existing CR2 → JPG batch converter so that:

1. The script is fully in English (code, comments, docstrings, user-facing strings).
2. It offers a friendly interactive CLI suitable for a Python-beginner end user (the author's wife) on macOS and Windows.
3. The project ships with a README and a dependency manifest so the user can install and run it from scratch.

The current script (`main.py`) already works correctly; this is a rewrite of the surface, not the conversion logic.

## Non-goals

- Changing the underlying conversion pipeline (rawpy postprocessing parameters stay the same).
- Supporting RAW formats other than CR2.
- Building a GUI.
- Packaging as a standalone executable.

## Directory layout

```
photo_converter/
├── main.py                # rewritten, English, interactive + argparse modes
├── requirements.txt       # rawpy, imageio, rich
├── pyproject.toml         # same deps in modern format
├── README.md              # macOS + Windows install/usage instructions
├── example/13.CR2         # unchanged sample input
└── docs/superpowers/specs/2026-05-22-photo-converter-english-cli-design.md
```

## `main.py` behavior

### Two modes, selected by argv

- **No arguments** → **interactive mode**: the script prompts for inputs one at a time. This is the primary mode for the end user.
- **One or more positional arguments** → **classic argparse mode**: preserved for power users / scripting.

### Interactive mode prompts (in order)

1. `Folder with CR2 files:` — required. Re-prompts until the path exists and is a directory.
2. `Output folder (press Enter to use the input folder):` — optional. Empty input falls back to the input folder.
3. `JPG quality 1-100 [92]:` — optional. Empty input → 92. Invalid input re-prompts.
4. `Include subfolders? [y/N]:` — optional. Empty → no. Accepts `y`/`yes`/`n`/`no`, case-insensitive.

Overwrite-existing is **not** prompted in interactive mode; it stays off (safe default). Power users can enable it via the `--overwrite` flag in argparse mode.

### Argparse mode

```
python main.py INPUT_FOLDER [OUTPUT_FOLDER] [--quality N] [--recursive] [--overwrite] [--workers N]
```

- `INPUT_FOLDER` — required positional.
- `OUTPUT_FOLDER` — optional positional, defaults to `INPUT_FOLDER`.
- `--quality N` — int 1–100, default 92.
- `--recursive` — search subfolders.
- `--overwrite` — overwrite existing JPGs (default: skip).
- `--workers N` — number of parallel workers (default: number of CPU cores).

### Output (both modes), driven by `rich`

- A `rich.progress.Progress` bar with item count and ETA during the loop.
- Per-file status lines using colored markers: green `✓` for converted, yellow `⊘` for skipped, red `✗` for error.
- A `rich.table.Table` summary at the end with rows: Converted / Skipped / Errors / Elapsed.
- Errors print the exception message inline and continue with the next file (current behavior preserved).

### Parallelism

- `rawpy.postprocess` is CPU-bound, so conversion runs across multiple cores via `concurrent.futures.ProcessPoolExecutor`.
- Default worker count: `os.cpu_count()` (falls back to 2 if unknown).
- Skip-checks (existing JPG present + no `--overwrite`) are evaluated synchronously up front so the skip log lines stay grouped and the worker pool only handles real work.
- Completion order of `✓`/`✗` lines is non-deterministic (whichever worker finishes first prints first); the progress bar advances as each future resolves.
- Argparse mode exposes `--workers N` to override the default. Interactive mode does not prompt for it — it always uses the default.

### Conversion function

Unchanged semantics. The function takes `(source_path, target_path, quality)` and uses the same `rawpy.postprocess` parameters as today:

- `use_camera_wb=True`
- `no_auto_bright=False`
- `output_bps=8`
- `highlight_mode=rawpy.HighlightMode.Blend`

Output is written via `imageio.imwrite` at the requested quality. The function creates parent directories as needed.

### File discovery

- Glob pattern: `**/*` if recursive, else `*`.
- Match files with `suffix.lower() == ".cr2"`.
- Sort results for deterministic ordering.
- Subfolder structure is preserved relative to the input folder when writing outputs.

## Dependencies

`requirements.txt`:

```
rawpy>=0.18
imageio>=2.0
rich>=13.0
```

`pyproject.toml` lists the same three dependencies under `[project]` with `requires-python = ">=3.9"`. No build backend is required for users; the file documents the project and makes `pip install .` work for those who prefer it.

If `rawpy`, `imageio`, or `rich` is missing at runtime, the script prints a single friendly message pointing at `pip install -r requirements.txt` and exits with code 1.

## README.md

Sections, in order:

1. **What it does** — one or two sentences.
2. **Install on macOS** — open Terminal, check Python version, create venv, activate, `pip install -r requirements.txt`.
3. **Install on Windows** — install Python from python.org (check "Add Python to PATH"), open PowerShell, create venv, activate, install.
4. **How to use** — primary path is "run `python main.py` and answer the questions"; secondary blurb mentions the argparse form for power users with one example.
5. **Troubleshooting** — at minimum: "command not found: python" (use `python3` on mac), Windows execution policy when activating venv, rawpy install failure on Apple Silicon (suggest upgrading pip).

## Error handling

- Missing input folder in argparse mode → friendly message, exit 1.
- Missing dependencies → friendly install hint, exit 1.
- Per-file conversion errors → logged with red `✗` and the exception message; loop continues.
- Ctrl-C during the loop → let `KeyboardInterrupt` propagate; the summary is not required to print on interrupt.

## Testing

This is a small single-file utility with an external native dependency (`rawpy`) and a sample input already present (`example/13.CR2`). Verification is manual:

- Run `python main.py` with no args, point it at `example/`, accept defaults, confirm `example/13.jpg` is produced and `rich` renders properly.
- Run `python main.py example/ --quality 85` and confirm argparse mode works.
- Run a second time without `--overwrite` and confirm the file is skipped.

No automated test suite is added in this iteration.
