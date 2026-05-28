# Photo Converter

[![CI](https://github.com/feleko/cr2-to-jpg/actions/workflows/ci.yml/badge.svg)](https://github.com/feleko/cr2-to-jpg/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/feleko/cr2-to-jpg)](LICENSE)

Batch-convert Canon **CR2** RAW photos to **JPG**. Comes with an interactive prompt — just run it and answer the questions.

## What it does

Given a folder of `.CR2` files, it produces a `.jpg` for each one using the camera's white balance and a gentle highlight recovery. By default it skips files that would overwrite an existing JPG in the output folder, so you can re-run it safely. Conversion runs in parallel across all CPU cores, so a batch of a few hundred photos finishes in a fraction of the single-threaded time.

## Install — macOS

1. Open **Terminal** (Applications → Utilities → Terminal).
2. Check Python is installed:

   ```bash
   python3 --version
   ```

   If it prints `Python 3.9` or newer, you're good. If not, install it from <https://www.python.org/downloads/macos/>.

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

1. Install **Python 3.9 or newer** from <https://www.python.org/downloads/windows/>.
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

Next time you want to use it, just open PowerShell, `cd` into the folder, and run `.\.venv\Scripts\Activate.ps1` before `python main.py`.

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

Note: interactive mode always skips existing JPGs and uses all CPU cores. If you need to overwrite existing files or limit the number of parallel workers, use the argument form below.

### The fast way (arguments)

If you prefer to type everything at once:

```bash
python main.py path/to/cr2s path/to/output --quality 85 --recursive
```

Available flags:

- `--quality N` — JPG quality 1–100, default 92.
- `--recursive` — also search subfolders. When you pass a separate output folder, the input's subfolder structure is preserved (e.g., `input/a/b/x.CR2` → `output/a/b/x.jpg`).
- `--overwrite` — overwrite existing JPGs (otherwise they're skipped).
- `--workers N` — number of parallel workers (default: all CPU cores). Use a smaller number if the computer becomes too sluggish to use while converting.

Run `python main.py --help` to see this again.

### Try the sample

A sample CR2 file is included in this repo at `example/13.CR2`. To smoke-test your install:

```bash
python main.py example
```

This will produce `example/13.jpg` next to it.

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

## Running tests (optional)

For development. Install the dev dependencies once:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
pytest
```
