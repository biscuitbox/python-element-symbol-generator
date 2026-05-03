#!/usr/bin/env python3
"""Generate element tiles as STL files via OpenSCAD.

Two entry points:
- `generate_tiles(...)` — programmatic API used by gui.py
- `main()` — CLI for batch generation from a .csv / .tsv file

Supported input formats for the CLI:
- .csv (recommended)
- .tsv

Expected columns (Korean or English):
- symbol (기호)
- name (이름)
- number (원자량)
- atomic_number (원자번호)
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

COLUMN_ALIASES = {
    "symbol": ["symbol", "기호"],
    "name": ["name", "이름", "원소명"],
    "number": ["number", "원자량"],
    "atomic_number": ["atomic_number", "원자번호", "atomic number"],
}


@dataclass
class TileParams:
    """Override values that get injected into the wrapper SCAD."""
    font_family: str = "NanumGothic"
    font_style: str = "Regular"  # Regular / Bold / ExtraBold / ...
    text_thicken: float = 0.0
    text_height: float = 0.6
    symbol_size: float = 25.0
    name_size: float = 7.0
    number_size: float = 7.0
    atomic_size: float = 7.0
    tile_size: float = 80.0
    base_thickness: float = 4.0
    fit_clearance: float = 0.15

    def font_name(self) -> str:
        style = (self.font_style or "Regular").strip()
        if not style or style.lower() == "regular":
            return f"{self.font_family}:style=Regular"
        return f"{self.font_family}:style={style}"

    def to_scad_lines(self) -> list[str]:
        return [
            f"font_name = \"{escape_scad_string(self.font_name())}\";",
            f"text_thicken = {self.text_thicken};",
            f"text_height = {self.text_height};",
            f"symbol_size = {self.symbol_size};",
            f"name_size = {self.name_size};",
            f"number_size = {self.number_size};",
            f"atomic_size = {self.atomic_size};",
            f"tile_size = {self.tile_size};",
            f"base_thickness = {self.base_thickness};",
            f"fit_clearance = {self.fit_clearance};",
        ]


@dataclass
class Element:
    symbol: str
    name: str
    number: str
    atomic_number: str

    @property
    def filename_stem(self) -> str:
        an = sanitize_filename(self.atomic_number)
        sym = sanitize_filename(self.symbol)
        return f"{an}_{sym}" if an else sym


def find_column(fieldnames: list[str], aliases: list[str]) -> str:
    lower_map = {c.strip().lower(): c for c in fieldnames}
    for alias in aliases:
        key = alias.strip().lower()
        if key in lower_map:
            return lower_map[key]
    raise ValueError(f"Missing one of columns: {aliases}")


def sanitize_filename(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    return text or "element"


def escape_scad_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\"", "\\\"")


def load_rows(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".tsv"}:
        raise ValueError("Only .csv and .tsv are supported in this environment.")

    delimiter = "," if suffix == ".csv" else "\t"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Input file has no header row.")
        return list(reader)


def rows_to_elements(rows: Iterable[dict[str, str]]) -> list[Element]:
    rows = list(rows)
    if not rows:
        return []
    fields = list(rows[0].keys())
    symbol_col = find_column(fields, COLUMN_ALIASES["symbol"])
    name_col = find_column(fields, COLUMN_ALIASES["name"])
    number_col = find_column(fields, COLUMN_ALIASES["number"])
    atomic_col = find_column(fields, COLUMN_ALIASES["atomic_number"])
    out: list[Element] = []
    for row in rows:
        sym = str(row.get(symbol_col, "")).strip()
        if not sym:
            continue
        out.append(Element(
            symbol=sym,
            name=str(row.get(name_col, "")).strip(),
            number=str(row.get(number_col, "")).strip(),
            atomic_number=str(row.get(atomic_col, "")).strip(),
        ))
    return out


def generate_tiles(
    elements: list[Element],
    out_dir: Path,
    *,
    scad_template: Path,
    openscad: str = "openscad",
    params: TileParams | None = None,
    on_progress: Callable[[int, int, Element, Path], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[Path]:
    """Generate STL files for the given elements.

    Returns the list of generated STL paths.

    Sidesteps two Windows-specific OpenSCAD issues by:
    (1) staging the SCAD template into an ASCII-only temp directory, and
    (2) passing all parameters via a UTF-8 wrapper file, never via -D.
    """
    if params is None:
        params = TileParams()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scad_template = Path(scad_template).resolve()
    if not scad_template.exists():
        raise FileNotFoundError(f"SCAD template not found: {scad_template}")

    generated: list[Path] = []
    common_params = "\n".join(params.to_scad_lines())

    with tempfile.TemporaryDirectory(prefix="element_tile_") as tmp:
        tmp_dir = Path(tmp)
        shutil.copy(scad_template, tmp_dir / "element_tiles.scad")

        total = len(elements)
        for index, el in enumerate(elements, start=1):
            if cancel_check and cancel_check():
                break

            outfile = out_dir / f"{el.filename_stem}.stl"
            wrapper = tmp_dir / f"_wrap_{el.filename_stem}.scad"
            wrapper.write_text(
                "include <element_tiles.scad>\n"
                f"symbol = \"{escape_scad_string(el.symbol)}\";\n"
                f"name = \"{escape_scad_string(el.name)}\";\n"
                f"number = \"{escape_scad_string(el.number)}\";\n"
                f"atomic_number = \"{escape_scad_string(el.atomic_number)}\";\n"
                f"{common_params}\n",
                encoding="utf-8",
            )

            cmd = [openscad, "-o", str(outfile), str(wrapper)]
            subprocess.run(cmd, check=True, capture_output=True)
            generated.append(outfile)

            if on_progress:
                on_progress(index, total, el, outfile)

    return generated


def render_preview_png(
    element: Element,
    out_png: Path,
    *,
    scad_template: Path,
    openscad: str = "openscad",
    params: TileParams | None = None,
    img_size: tuple[int, int] = (640, 640),
) -> Path:
    """Render a quick PNG preview of a single tile."""
    if params is None:
        params = TileParams()

    scad_template = Path(scad_template).resolve()
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    common_params = "\n".join(params.to_scad_lines())

    with tempfile.TemporaryDirectory(prefix="element_preview_") as tmp:
        tmp_dir = Path(tmp)
        shutil.copy(scad_template, tmp_dir / "element_tiles.scad")
        wrapper = tmp_dir / "_preview.scad"
        wrapper.write_text(
            "include <element_tiles.scad>\n"
            f"symbol = \"{escape_scad_string(element.symbol)}\";\n"
            f"name = \"{escape_scad_string(element.name)}\";\n"
            f"number = \"{escape_scad_string(element.number)}\";\n"
            f"atomic_number = \"{escape_scad_string(element.atomic_number)}\";\n"
            f"{common_params}\n",
            encoding="utf-8",
        )
        cmd = [
            openscad, "-o", str(out_png),
            f"--imgsize={img_size[0]},{img_size[1]}",
            "--autocenter", "--viewall", "--projection=ortho",
            str(wrapper),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    return out_png


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("table", help="Path to .csv or .tsv file")
    parser.add_argument("--scad", default="element_tiles.scad", help="Path to SCAD template")
    parser.add_argument("--out", default="out", help="Output directory for STL files")
    parser.add_argument("--openscad", default="openscad", help="OpenSCAD executable")
    args = parser.parse_args()

    rows = load_rows(Path(args.table))
    elements = rows_to_elements(rows)
    if not elements:
        raise ValueError("Input file has no usable rows.")

    def progress(i: int, total: int, el: Element, outfile: Path) -> None:
        print(f"[{i}/{total}] {outfile.name}  ({el.symbol} / {el.name})")

    generate_tiles(
        elements,
        Path(args.out),
        scad_template=Path(args.scad),
        openscad=args.openscad,
        on_progress=progress,
    )


if __name__ == "__main__":
    main()
