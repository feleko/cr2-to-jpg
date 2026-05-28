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


def convert_file(source: Path, target: Path, quality: int) -> float:
    """Convert a single CR2 file to JPG using the camera's white balance.

    Returns the elapsed wall-clock time in seconds.
    """
    start = time.monotonic()
    with rawpy.imread(str(source)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=False,
            output_bps=8,
            highlight_mode=rawpy.HighlightMode.Blend,
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(str(target), rgb, format="JPEG", quality=quality)
    return time.monotonic() - start


def find_cr2_files(folder: Path, recursive: bool) -> list[Path]:
    """Return CR2 files in `folder`, sorted, case-insensitive on extension."""
    pattern = "**/*" if recursive else "*"
    return sorted(
        p for p in folder.glob(pattern)
        if p.is_file() and p.suffix.lower() == ".cr2"
    )


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
        pool = ProcessPoolExecutor(max_workers=worker_count)
        try:
            with progress:
                task_id = progress.add_task("Converting", total=len(jobs))
                futures = {
                    pool.submit(convert_file, src, tgt, quality): (src, tgt)
                    for src, tgt in jobs
                }
                for future in as_completed(futures):
                    src, tgt = futures[future]
                    try:
                        file_elapsed = future.result()
                        progress.console.print(
                            f"[green]✓[/green] {src.name} → {tgt.name} "
                            f"[dim]({file_elapsed:.1f}s)[/dim]"
                        )
                        converted += 1
                    except Exception as e:
                        progress.console.print(f"[red]✗[/red] {src.name}: {e}")
                        errors += 1
                    progress.advance(task_id)
            pool.shutdown(wait=True)
        except KeyboardInterrupt:
            console.print("[yellow]Interrupted. Cancelling remaining work…[/yellow]")
            pool.shutdown(wait=False, cancel_futures=True)
            raise

    elapsed = time.time() - start
    print_summary(converted, skipped, errors, elapsed)


def _unquote(text: str) -> str:
    """Strip a single matching pair of surrounding quotes, if present."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1]
    return text


def prompt_input_folder() -> Path:
    """Ask for the input folder; re-prompt until the path is a real directory."""
    while True:
        raw = _unquote(input("Folder with CR2 files: "))
        if not raw:
            console.print("[red]Please enter a path.[/red]")
            continue
        path = Path(raw).expanduser()
        if not path.is_dir():
            console.print(f"[red]'{path}' is not a folder. Try again.[/red]")
            continue
        return path


def prompt_output_folder(default: Path) -> Path:
    """Ask for the output folder; empty input falls back to `default`."""
    raw = _unquote(input(f"Output folder (press Enter to use '{default}'): "))
    if not raw:
        return default
    return Path(raw).expanduser()


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


def prompt_recursive() -> bool:
    """Ask whether to descend into subfolders; default no."""
    while True:
        raw = input("Include subfolders? [y/N]: ").strip().lower()
        if raw in ("", "n", "no"):
            return False
        if raw in ("y", "yes"):
            return True
        console.print("[red]Please answer y or n.[/red]")


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

    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")

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


def main() -> None:
    if len(sys.argv) > 1:
        run_with_args(sys.argv[1:])
    else:
        run_interactive()


if __name__ == "__main__":
    main()
