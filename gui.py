"""Tkinter GUI for the element tile generator.

Run with `python gui.py` from the maru-python-version folder, or just
double-click `타일생성기.bat`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
import traceback
from dataclasses import asdict
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, messagebox, ttk

from generate_tiles import (
    Element,
    TileParams,
    generate_tiles,
    load_rows,
    rows_to_elements,
)
from periodic_table import CATEGORY_INFO, ELEMENTS, PLACEHOLDERS, PTEntry

APP_TITLE = "원소 타일 생성기"
APP_DIR = Path(__file__).resolve().parent
SCAD_TEMPLATE = APP_DIR / "element_tiles.scad"
CONFIG_DIR = Path.home() / ".element_tile_generator"
CONFIG_PATH = CONFIG_DIR / "config.json"
PRESETS_DIR = CONFIG_DIR / "presets"

# Chemistry-textbook palette
COLOR_BG = "#F5F1E8"          # warm cream
COLOR_PANEL = "#FFFFFF"        # paper white
COLOR_HEADER_BG = "#1B3A5C"    # deep ink blue
COLOR_HEADER_FG = "#F5F1E8"
COLOR_ACCENT = "#1F6E8C"       # flask teal
COLOR_ACCENT_HOVER = "#2A8AAB"
COLOR_TEXT = "#1A1A1A"
COLOR_MUTED = "#6F6F6F"
COLOR_BORDER = "#C8B98F"       # parchment border
COLOR_SELECTED = "#1F6E8C"     # selection ring

# Korean fonts that allow commercial redistribution + Hangul support.
# Keys are family names exactly as Tk / OpenSCAD see them on Windows.
KOREAN_COMMERCIAL_FONTS: dict[str, str] = {
    "NanumGothic":            "나눔고딕",
    "NanumGothicBold":        "나눔고딕 (Bold 패밀리)",
    "NanumMyeongjo":          "나눔명조",
    "NanumBarunGothic":       "나눔바른고딕",
    "NanumSquare":            "나눔스퀘어",
    "NanumSquareRound":       "나눔스퀘어 라운드",
    "Pretendard":             "프리텐다드",
    "Pretendard Variable":    "프리텐다드 (가변)",
    "Noto Sans KR":           "본고딕 (Noto Sans KR)",
    "Noto Sans CJK KR":       "본고딕 (Noto Sans CJK KR)",
    "Noto Serif KR":          "본명조 (Noto Serif KR)",
    "S-Core Dream":           "에스코어 드림",
    "Cafe24Ssurround":        "카페24 써라운드",
    "Cafe24Oneprettynight":   "카페24 원프리티나잇",
    "BMHANNAPro":             "배민 한나 Pro",
    "BM HANNA Pro":           "배민 한나 Pro",
    "BMDOHYEON":              "배민 도현",
    "BM DOHYEON":             "배민 도현",
    "BMJUA":                  "배민 주아",
    "BM JUA":                 "배민 주아",
    "Gowun Dodum":            "고운 돋움",
    "Gowun Batang":           "고운 바탕",
}

FONT_STYLES = ["Regular", "Bold", "ExtraBold", "Light"]

DEFAULT_CONFIG = {
    "openscad_path": "",
    "out_dir": "",
    "auto_open": True,
    "play_sound": True,
    "params": asdict(TileParams()),
    "selected_numbers": [1, 2, 6, 8, 26, 52],
}


# ---------- helpers ----------

def find_openscad() -> str:
    candidates = [
        r"C:\Program Files\OpenSCAD\openscad.exe",
        r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
        str(Path.home() / "AppData" / "Local" / "Programs" / "OpenSCAD" / "openscad.exe"),
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    found = shutil.which("openscad")
    return found or ""


def list_installed_korean_fonts() -> list[tuple[str, str]]:
    available = set(tkfont.families())
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for family, label in KOREAN_COMMERCIAL_FONTS.items():
        if family in available and family not in seen:
            out.append((family, label))
            seen.add(family)
    if not any(f == "NanumGothic" for f, _ in out):
        out.insert(0, ("NanumGothic", "나눔고딕 (설치 필요할 수 있음)"))
    return out


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            merged["params"] = {**DEFAULT_CONFIG["params"], **data.get("params", {})}
            return merged
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def play_done_sound() -> None:
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        else:
            print("\a", end="")
    except Exception:
        pass


def open_folder(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


# ---------- periodic table widget ----------

class PeriodicTable(ttk.Frame):
    """Canvas-based periodic table with click-to-select cells."""

    CELL_SIZE = 46
    CELL_GAP = 3
    LANTH_GAP = 12  # extra space above lanthanide rows

    def __init__(self, parent: tk.Misc, on_change=None) -> None:
        super().__init__(parent, style="Card.TFrame")
        self.on_change = on_change
        self.selected: set[int] = set()
        self._items: dict[int, dict] = {}  # number -> {"rect", "text_top", ...}

        cols = 18
        rows_main = 7
        rows_lanth = 9
        width = self.CELL_SIZE * cols + self.CELL_GAP * (cols + 1) + 10
        height = (
            self.CELL_SIZE * rows_lanth
            + self.CELL_GAP * (rows_lanth + 1)
            + self.LANTH_GAP
            + 10
        )

        self.canvas = tk.Canvas(
            self, width=width, height=height,
            background=COLOR_PANEL, highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self._draw_cells()
        self._draw_placeholders()
        self.canvas.bind("<Button-1>", self._on_click)

    def _cell_xy(self, row: int, col: int) -> tuple[int, int]:
        x = 6 + (col - 1) * (self.CELL_SIZE + self.CELL_GAP)
        y = 6 + (row - 1) * (self.CELL_SIZE + self.CELL_GAP)
        if row >= 8:
            y += self.LANTH_GAP
        return x, y

    def _draw_cells(self) -> None:
        for el in ELEMENTS:
            self._draw_element(el)

    def _draw_element(self, el: PTEntry) -> None:
        x, y = self._cell_xy(el.row, el.col)
        size = self.CELL_SIZE
        color = CATEGORY_INFO[el.category][1]
        rect = self.canvas.create_rectangle(
            x, y, x + size, y + size,
            fill=color, outline="#7A7A7A", width=1,
            tags=(f"el-{el.number}", "cell"),
        )
        num = self.canvas.create_text(
            x + 4, y + 3, anchor="nw", text=str(el.number),
            font=("Segoe UI", 7), fill="#222222",
            tags=(f"el-{el.number}",),
        )
        sym = self.canvas.create_text(
            x + size / 2, y + size / 2 + 1, text=el.symbol,
            font=("Segoe UI", 13, "bold"), fill=COLOR_TEXT,
            tags=(f"el-{el.number}",),
        )
        nm = self.canvas.create_text(
            x + size / 2, y + size - 7, text=el.name,
            font=("Malgun Gothic", 7), fill="#333333",
            tags=(f"el-{el.number}",),
        )
        self._items[el.number] = {"rect": rect, "num": num, "sym": sym, "nm": nm}

    def _draw_placeholders(self) -> None:
        for row, col, label, category in PLACEHOLDERS:
            x, y = self._cell_xy(row, col)
            size = self.CELL_SIZE
            color = CATEGORY_INFO[category][1]
            self.canvas.create_rectangle(
                x, y, x + size, y + size,
                fill=color, outline="#9A9A9A", width=1, dash=(2, 2),
            )
            self.canvas.create_text(
                x + size / 2, y + size / 2, text=label,
                font=("Segoe UI", 8, "italic"), fill="#444444",
            )

    def _on_click(self, event) -> None:
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return
        tags = self.canvas.gettags(item[0])
        for tag in tags:
            if tag.startswith("el-"):
                try:
                    n = int(tag.split("-", 1)[1])
                except ValueError:
                    return
                self.toggle(n)
                return

    def toggle(self, number: int) -> None:
        if number in self.selected:
            self.selected.discard(number)
        else:
            self.selected.add(number)
        self._refresh_cell(number)
        if self.on_change:
            self.on_change()

    def _refresh_cell(self, number: int) -> None:
        item = self._items.get(number)
        if not item:
            return
        is_sel = number in self.selected
        self.canvas.itemconfigure(
            item["rect"],
            outline=COLOR_SELECTED if is_sel else "#7A7A7A",
            width=3 if is_sel else 1,
        )

    def select_all(self) -> None:
        self.selected = {e.number for e in ELEMENTS}
        for n in self._items:
            self._refresh_cell(n)
        if self.on_change:
            self.on_change()

    def clear(self) -> None:
        self.selected.clear()
        for n in self._items:
            self._refresh_cell(n)
        if self.on_change:
            self.on_change()

    def set_selected(self, numbers) -> None:
        self.selected = set(int(n) for n in numbers if int(n) in self._items)
        for n in self._items:
            self._refresh_cell(n)
        if self.on_change:
            self.on_change()


# ---------- main app ----------

class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = load_config()
        if not self.config.get("openscad_path"):
            self.config["openscad_path"] = find_openscad()

        self.csv_elements: list[Element] = []
        self.worker: threading.Thread | None = None
        self.cancel_flag = threading.Event()
        self.queue: Queue = Queue()

        self._setup_root()
        self._setup_styles()
        self._setup_vars()
        self._build_ui()
        self._restore_selection()
        self._update_action_state()
        self._update_selection_count()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_queue)

    # ----- setup -----

    def _setup_root(self) -> None:
        self.root.title(f"⚛  {APP_TITLE}")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(1000, 720)
        try:
            base = tkfont.nametofont("TkDefaultFont")
            base.configure(family="Malgun Gothic", size=10)
            text_font = tkfont.nametofont("TkTextFont")
            text_font.configure(family="Malgun Gothic", size=10)
        except Exception:
            pass

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=("Malgun Gothic", 10))
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_PANEL, relief="solid",
                        borderwidth=1, bordercolor=COLOR_BORDER)
        style.configure("Header.TFrame", background=COLOR_HEADER_BG)
        style.configure("Header.TLabel", background=COLOR_HEADER_BG,
                        foreground=COLOR_HEADER_FG, font=("Malgun Gothic", 16, "bold"))
        style.configure("HeaderSub.TLabel", background=COLOR_HEADER_BG,
                        foreground="#C9D9E5", font=("Malgun Gothic", 9))
        style.configure("Section.TLabel", background=COLOR_PANEL,
                        foreground=COLOR_ACCENT, font=("Malgun Gothic", 11, "bold"))
        style.configure("Card.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT)
        style.configure("Muted.TLabel", background=COLOR_PANEL, foreground=COLOR_MUTED,
                        font=("Malgun Gothic", 9))
        style.configure("Footer.TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
        style.configure("TLabelframe", background=COLOR_PANEL, foreground=COLOR_ACCENT,
                        font=("Malgun Gothic", 10, "bold"), bordercolor=COLOR_BORDER)
        style.configure("TLabelframe.Label", background=COLOR_PANEL, foreground=COLOR_ACCENT,
                        font=("Malgun Gothic", 10, "bold"))
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8),
                        font=("Malgun Gothic", 10, "bold"), background="#E5DDC8",
                        foreground=COLOR_TEXT)
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_PANEL)],
                  foreground=[("selected", COLOR_ACCENT)])
        style.configure("Primary.TButton",
                        background=COLOR_ACCENT, foreground="white",
                        font=("Malgun Gothic", 11, "bold"),
                        padding=(20, 10), borderwidth=0)
        style.map("Primary.TButton",
                  background=[("active", COLOR_ACCENT_HOVER), ("disabled", "#A8B5BC")])
        style.configure("Secondary.TButton", padding=(10, 6))
        style.configure("TCheckbutton", background=COLOR_PANEL)
        style.configure("Card.TCheckbutton", background=COLOR_PANEL)
        style.configure("Footer.TCheckbutton", background=COLOR_BG)
        style.configure("Horizontal.TProgressbar",
                        troughcolor="#E5DDC8", background=COLOR_ACCENT, thickness=16)

    def _setup_vars(self) -> None:
        p = self.config["params"]
        self.var_font_family = tk.StringVar(value=p.get("font_family", "NanumGothic"))
        self.var_font_style = tk.StringVar(value=p.get("font_style", "Regular"))
        self.var_text_thicken = tk.DoubleVar(value=p.get("text_thicken", 0.0))
        self.var_text_height = tk.DoubleVar(value=p.get("text_height", 0.6))
        self.var_symbol_size = tk.DoubleVar(value=p.get("symbol_size", 25.0))
        self.var_name_size = tk.DoubleVar(value=p.get("name_size", 7.0))
        self.var_number_size = tk.DoubleVar(value=p.get("number_size", 7.0))
        self.var_atomic_size = tk.DoubleVar(value=p.get("atomic_size", 7.0))
        self.var_tile_size = tk.DoubleVar(value=p.get("tile_size", 80.0))
        self.var_base_thickness = tk.DoubleVar(value=p.get("base_thickness", 4.0))
        self.var_fit_clearance = tk.DoubleVar(value=p.get("fit_clearance", 0.15))
        self.var_openscad = tk.StringVar(value=self.config.get("openscad_path", ""))
        self.var_out_dir = tk.StringVar(value=self.config.get("out_dir", str(APP_DIR / "out")))
        self.var_auto_open = tk.BooleanVar(value=self.config.get("auto_open", True))
        self.var_play_sound = tk.BooleanVar(value=self.config.get("play_sound", True))
        self.var_input_mode = tk.StringVar(value="periodic")  # periodic | csv
        self.var_csv_path = tk.StringVar(value="")

    def _build_ui(self) -> None:
        # Header band
        header = ttk.Frame(self.root, style="Header.TFrame")
        header.pack(side="top", fill="x")
        inner = ttk.Frame(header, style="Header.TFrame")
        inner.pack(padx=20, pady=12, anchor="w")
        ttk.Label(inner, text=f"⚛  {APP_TITLE}", style="Header.TLabel").pack(anchor="w")
        ttk.Label(inner, text="주기율표에서 원소를 골라 3D 프린팅용 STL 타일을 만듭니다.",
                  style="HeaderSub.TLabel").pack(anchor="w", pady=(2, 0))

        # Notebook
        nb_wrap = ttk.Frame(self.root)
        nb_wrap.pack(side="top", fill="both", expand=True, padx=14, pady=(12, 0))
        self.nb = ttk.Notebook(nb_wrap)
        self.nb.pack(fill="both", expand=True)

        self.tab_select = ttk.Frame(self.nb, style="Card.TFrame")
        self.tab_design = ttk.Frame(self.nb, style="Card.TFrame")
        self.tab_print = ttk.Frame(self.nb, style="Card.TFrame")
        self.tab_output = ttk.Frame(self.nb, style="Card.TFrame")
        self.nb.add(self.tab_select, text="① 원소 선택")
        self.nb.add(self.tab_design, text="② 글자 디자인")
        self.nb.add(self.tab_print, text="③ 인쇄 설정")
        self.nb.add(self.tab_output, text="④ 출력 설정")

        self._build_tab_select()
        self._build_tab_design()
        self._build_tab_print()
        self._build_tab_output()

        # Footer / actions
        footer = ttk.Frame(self.root, style="TFrame")
        footer.pack(side="bottom", fill="x", padx=14, pady=12)

        opts = ttk.Frame(footer, style="TFrame")
        opts.pack(side="top", fill="x")
        ttk.Checkbutton(opts, text="완료 시 결과 폴더 자동 열기",
                        variable=self.var_auto_open, style="Footer.TCheckbutton").pack(side="left", padx=(0, 16))
        ttk.Checkbutton(opts, text="완료 시 알림음",
                        variable=self.var_play_sound, style="Footer.TCheckbutton").pack(side="left")
        ttk.Button(opts, text="프리셋 저장", style="Secondary.TButton",
                   command=self._save_preset).pack(side="right", padx=4)
        ttk.Button(opts, text="프리셋 불러오기", style="Secondary.TButton",
                   command=self._load_preset).pack(side="right", padx=4)

        bar = ttk.Frame(footer, style="TFrame")
        bar.pack(side="top", fill="x", pady=(10, 0))
        self.progress = ttk.Progressbar(bar, mode="determinate", style="Horizontal.TProgressbar")
        self.progress.pack(side="top", fill="x")
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(bar, textvariable=self.status_var, style="Footer.TLabel").pack(side="top",
                                                                                  anchor="w", pady=(4, 0))

        action = ttk.Frame(footer, style="TFrame")
        action.pack(side="top", fill="x", pady=(8, 0))
        self.btn_generate = ttk.Button(action, text="🧪  STL 생성 시작",
                                        style="Primary.TButton", command=self._on_generate)
        self.btn_generate.pack(side="left")
        self.btn_cancel = ttk.Button(action, text="중단", style="Secondary.TButton",
                                      command=self._on_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=8)
        self.btn_open_out = ttk.Button(action, text="결과 폴더 열기",
                                        style="Secondary.TButton",
                                        command=lambda: open_folder(Path(self.var_out_dir.get())))
        self.btn_open_out.pack(side="left", padx=8)

    # ----- tab: select -----

    def _build_tab_select(self) -> None:
        wrap = ttk.Frame(self.tab_select, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        mode_bar = ttk.Frame(wrap, style="Card.TFrame")
        mode_bar.pack(fill="x", pady=(0, 8))
        ttk.Radiobutton(mode_bar, text="주기율표에서 선택", value="periodic",
                        variable=self.var_input_mode, command=self._on_mode_change,
                        style="Card.TCheckbutton").pack(side="left", padx=(0, 16))
        ttk.Radiobutton(mode_bar, text="CSV 파일 사용", value="csv",
                        variable=self.var_input_mode, command=self._on_mode_change,
                        style="Card.TCheckbutton").pack(side="left")

        self.frame_periodic = ttk.Frame(wrap, style="Card.TFrame")
        self.frame_periodic.pack(fill="both", expand=True)

        self.pt = PeriodicTable(self.frame_periodic, on_change=self._update_selection_count)
        self.pt.pack(side="top")

        bottom = ttk.Frame(self.frame_periodic, style="Card.TFrame")
        bottom.pack(fill="x", pady=(8, 0))
        self.lbl_count = ttk.Label(bottom, text="0개 선택됨", style="Section.TLabel")
        self.lbl_count.pack(side="left", padx=4)
        ttk.Button(bottom, text="전체 선택", style="Secondary.TButton",
                   command=self.pt.select_all).pack(side="right", padx=4)
        ttk.Button(bottom, text="전체 해제", style="Secondary.TButton",
                   command=self.pt.clear).pack(side="right", padx=4)
        ttk.Button(bottom, text="중학교 권장 (H, He, C, N, O, Na, Mg, Al, Si, S, Cl, K, Ca, Fe, Cu)",
                   style="Secondary.TButton",
                   command=self._select_school_set).pack(side="right", padx=4)

        self._build_legend(self.frame_periodic)

        self.frame_csv = ttk.Frame(wrap, style="Card.TFrame")
        row = ttk.Frame(self.frame_csv, style="Card.TFrame")
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="CSV 파일:", style="Card.TLabel").pack(side="left")
        ttk.Entry(row, textvariable=self.var_csv_path, width=60).pack(side="left", padx=8, fill="x", expand=True)
        ttk.Button(row, text="찾아보기", style="Secondary.TButton",
                   command=self._browse_csv).pack(side="left")
        self.csv_status = ttk.Label(self.frame_csv, text="(파일을 선택하세요)", style="Muted.TLabel")
        self.csv_status.pack(anchor="w", pady=(4, 0))

    def _build_legend(self, parent: tk.Misc) -> None:
        legend = ttk.Frame(parent, style="Card.TFrame")
        legend.pack(fill="x", pady=(8, 0))
        ttk.Label(legend, text="범례", style="Section.TLabel").pack(side="left", padx=(2, 12))
        for key, (label, color) in CATEGORY_INFO.items():
            chip = ttk.Frame(legend, style="Card.TFrame")
            chip.pack(side="left", padx=4, pady=2)
            sw = tk.Frame(chip, width=14, height=14, bg=color, highlightthickness=1,
                          highlightbackground="#888888")
            sw.pack(side="left", padx=(0, 4))
            ttk.Label(chip, text=label, style="Card.TLabel",
                      font=("Malgun Gothic", 9)).pack(side="left")

    # ----- tab: design -----

    def _build_tab_design(self) -> None:
        wrap = ttk.Frame(self.tab_design, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        # Font block
        f1 = ttk.LabelFrame(wrap, text="  글꼴  ", padding=12)
        f1.pack(fill="x", pady=(0, 12))

        fonts = list_installed_korean_fonts()
        self.font_map: dict[str, str] = {}
        font_display = []
        for family, label in fonts:
            display = f"{label}  —  {family}"
            font_display.append(display)
            self.font_map[display] = family

        current_family = self.var_font_family.get()
        current_display = next(
            (d for d, f in self.font_map.items() if f == current_family),
            font_display[0] if font_display else current_family,
        )

        ttk.Label(f1, text="폰트 (상업 이용 가능 + 한글)", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.cb_font = ttk.Combobox(f1, values=font_display, state="readonly", width=42)
        self.cb_font.set(current_display)
        self.cb_font.bind("<<ComboboxSelected>>", self._on_font_pick)
        self.cb_font.grid(row=0, column=1, sticky="w")

        ttk.Label(f1, text="굵기", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.cb_weight = ttk.Combobox(f1, values=FONT_STYLES, state="readonly",
                                      textvariable=self.var_font_style, width=18)
        self.cb_weight.grid(row=1, column=1, sticky="w", pady=(8, 0))

        self._spin(f1, "추가로 굵게 (mm)", self.var_text_thicken, 0.0, 0.5, 0.02,
                   row=2, hint="0=폰트 그대로, 0.05~0.15 권장 (각인 가독성↑)")

        # Sizes block
        f2 = ttk.LabelFrame(wrap, text="  글자 크기 / 깊이  ", padding=12)
        f2.pack(fill="x", pady=(0, 12))
        self._spin(f2, "기호 크기 (mm)", self.var_symbol_size, 5, 60, 0.5, row=0)
        self._spin(f2, "이름 크기 (mm)", self.var_name_size, 3, 20, 0.5, row=1)
        self._spin(f2, "원자량 크기 (mm)", self.var_number_size, 3, 20, 0.5, row=2)
        self._spin(f2, "원자번호 크기 (mm)", self.var_atomic_size, 3, 20, 0.5, row=3)
        self._spin(f2, "각인 깊이 (mm)", self.var_text_height, 0.2, 2.0, 0.1, row=4,
                   hint="얼마나 도드라지게 새길지. 0.6~1.0 권장")

        ttk.Label(wrap, text="※ 글자 크기는 타일에 새겨지는 실제 mm 크기입니다.",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    # ----- tab: print -----

    def _build_tab_print(self) -> None:
        wrap = ttk.Frame(self.tab_print, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        f1 = ttk.LabelFrame(wrap, text="  타일 치수  ", padding=12)
        f1.pack(fill="x", pady=(0, 12))
        self._spin(f1, "타일 한 변 (mm)", self.var_tile_size, 30, 200, 1, row=0,
                   hint="정사각형. 학교 수업용은 60~90mm 권장")
        self._spin(f1, "타일 두께 (mm)", self.var_base_thickness, 2, 10, 0.2, row=1,
                   hint="너무 얇으면 휨, 두꺼우면 출력 시간↑")

        f2 = ttk.LabelFrame(wrap, text="  결합부 (옆 타일과 끼움)  ", padding=12)
        f2.pack(fill="x", pady=(0, 12))
        self._spin(f2, "끼움 여유 (mm)", self.var_fit_clearance, 0.05, 0.30, 0.01, row=0,
                   hint="작을수록 빡빡 / 클수록 헐렁. 0.15 기본")

    # ----- tab: output -----

    def _build_tab_output(self) -> None:
        wrap = ttk.Frame(self.tab_output, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        f1 = ttk.LabelFrame(wrap, text="  OpenSCAD 위치  ", padding=12)
        f1.pack(fill="x", pady=(0, 12))
        row1 = ttk.Frame(f1, style="Card.TFrame")
        row1.pack(fill="x")
        ttk.Entry(row1, textvariable=self.var_openscad).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(row1, text="자동 탐지", style="Secondary.TButton",
                   command=self._auto_detect_openscad).pack(side="left", padx=2)
        ttk.Button(row1, text="찾아보기", style="Secondary.TButton",
                   command=self._browse_openscad).pack(side="left", padx=2)
        ttk.Label(f1, text="처음 한 번만 설정하면 됩니다 (보통 자동 탐지로 충분).",
                  style="Muted.TLabel").pack(anchor="w", pady=(6, 0))

        f2 = ttk.LabelFrame(wrap, text="  결과 폴더  ", padding=12)
        f2.pack(fill="x", pady=(0, 12))
        row2 = ttk.Frame(f2, style="Card.TFrame")
        row2.pack(fill="x")
        ttk.Entry(row2, textvariable=self.var_out_dir).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(row2, text="찾아보기", style="Secondary.TButton",
                   command=self._browse_out).pack(side="left")

    # ----- small builders -----

    def _spin(self, parent, label, var, mn, mx, inc, *, row, hint: str | None = None) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        sb = ttk.Spinbox(parent, from_=mn, to=mx, increment=inc, textvariable=var, width=10, format="%.2f")
        sb.grid(row=row, column=1, sticky="w", pady=3)
        if hint:
            ttk.Label(parent, text=hint, style="Muted.TLabel").grid(row=row, column=2, sticky="w", padx=8)

    # ----- callbacks -----

    def _on_font_pick(self, _evt) -> None:
        display = self.cb_font.get()
        family = self.font_map.get(display)
        if family:
            self.var_font_family.set(family)

    def _on_mode_change(self) -> None:
        if self.var_input_mode.get() == "periodic":
            self.frame_csv.pack_forget()
            self.frame_periodic.pack(fill="both", expand=True)
        else:
            self.frame_periodic.pack_forget()
            self.frame_csv.pack(fill="both", expand=True, padx=4, pady=4)
        self._update_action_state()

    def _select_school_set(self) -> None:
        self.pt.set_selected({1, 2, 6, 7, 8, 11, 12, 13, 14, 16, 17, 19, 20, 26, 29})

    def _update_selection_count(self) -> None:
        n = len(self.pt.selected)
        self.lbl_count.configure(text=f"{n}개 선택됨")
        self._update_action_state()

    def _restore_selection(self) -> None:
        self.pt.set_selected(self.config.get("selected_numbers", []))

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="CSV / TSV 파일 선택",
            filetypes=[("CSV / TSV", "*.csv *.tsv"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            rows = load_rows(Path(path))
            self.csv_elements = rows_to_elements(rows)
            self.var_csv_path.set(path)
            self.csv_status.configure(text=f"{len(self.csv_elements)}개 행 로드됨")
        except Exception as e:
            messagebox.showerror("CSV 오류", f"CSV를 읽지 못했습니다:\n{e}", parent=self.root)
        self._update_action_state()

    def _browse_openscad(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="OpenSCAD 실행 파일 선택",
            filetypes=[("실행 파일", "*.exe"), ("모든 파일", "*.*")])
        if path:
            self.var_openscad.set(path)
            self._update_action_state()

    def _auto_detect_openscad(self) -> None:
        path = find_openscad()
        if path:
            self.var_openscad.set(path)
            messagebox.showinfo("탐지 완료", f"OpenSCAD을 찾았습니다:\n{path}", parent=self.root)
        else:
            messagebox.showwarning("탐지 실패",
                                   "OpenSCAD을 찾지 못했습니다. '찾아보기'로 직접 선택해주세요.\n"
                                   "(설치되지 않았다면 https://openscad.org/downloads.html 에서 받으세요.)",
                                   parent=self.root)
        self._update_action_state()

    def _browse_out(self) -> None:
        path = filedialog.askdirectory(parent=self.root, title="결과 폴더 선택",
                                       initialdir=self.var_out_dir.get() or str(APP_DIR))
        if path:
            self.var_out_dir.set(path)

    def _save_preset(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root, title="프리셋 저장",
            defaultextension=".json", initialdir=str(PRESETS_DIR),
            filetypes=[("프리셋 JSON", "*.json")])
        if not path:
            return
        try:
            PRESETS_DIR.mkdir(parents=True, exist_ok=True)
            data = self._collect_config()
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("저장 완료", "프리셋을 저장했습니다.", parent=self.root)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e), parent=self.root)

    def _load_preset(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="프리셋 불러오기",
            initialdir=str(PRESETS_DIR), filetypes=[("프리셋 JSON", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self._apply_config(data)
            messagebox.showinfo("불러옴", "프리셋을 적용했습니다.", parent=self.root)
        except Exception as e:
            messagebox.showerror("불러오기 실패", str(e), parent=self.root)

    # ----- generation -----

    def _selected_elements(self) -> list[Element]:
        if self.var_input_mode.get() == "csv":
            return list(self.csv_elements)
        out = []
        for n in sorted(self.pt.selected):
            e = next((x for x in ELEMENTS if x.number == n), None)
            if e:
                out.append(Element(symbol=e.symbol, name=e.name,
                                   number=e.weight, atomic_number=str(e.number)))
        return out

    def _update_action_state(self) -> None:
        ready = (
            bool(self.var_openscad.get())
            and Path(self.var_openscad.get()).exists()
            and bool(self._selected_elements())
        )
        self.btn_generate.configure(state="normal" if ready else "disabled")

    def _on_generate(self) -> None:
        elements = self._selected_elements()
        if not elements:
            messagebox.showwarning("선택 없음", "원소를 1개 이상 선택해주세요.", parent=self.root)
            return
        openscad = self.var_openscad.get()
        if not openscad or not Path(openscad).exists():
            messagebox.showerror("OpenSCAD 없음",
                                 "OpenSCAD 실행 파일 경로를 ④번 탭에서 설정해주세요.",
                                 parent=self.root)
            return
        out_dir = Path(self.var_out_dir.get() or APP_DIR / "out")

        params = TileParams(
            font_family=self.var_font_family.get(),
            font_style=self.var_font_style.get(),
            text_thicken=float(self.var_text_thicken.get()),
            text_height=float(self.var_text_height.get()),
            symbol_size=float(self.var_symbol_size.get()),
            name_size=float(self.var_name_size.get()),
            number_size=float(self.var_number_size.get()),
            atomic_size=float(self.var_atomic_size.get()),
            tile_size=float(self.var_tile_size.get()),
            base_thickness=float(self.var_base_thickness.get()),
            fit_clearance=float(self.var_fit_clearance.get()),
        )

        self.cancel_flag.clear()
        self.progress.configure(maximum=len(elements), value=0)
        self.status_var.set(f"생성 중... 0 / {len(elements)}")
        self.btn_generate.configure(state="disabled")
        self.btn_cancel.configure(state="normal")

        self.worker = threading.Thread(
            target=self._worker_run,
            args=(elements, out_dir, openscad, params),
            daemon=True,
        )
        self.worker.start()

    def _worker_run(self, elements, out_dir, openscad, params) -> None:
        try:
            def on_prog(i, total, el, outfile):
                self.queue.put(("progress", i, total, el.symbol, el.name))

            generated = generate_tiles(
                elements, Path(out_dir),
                scad_template=SCAD_TEMPLATE,
                openscad=openscad, params=params,
                on_progress=on_prog,
                cancel_check=self.cancel_flag.is_set,
            )
            cancelled = self.cancel_flag.is_set()
            self.queue.put(("done", len(generated), len(elements), cancelled, str(out_dir)))
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or b"").decode("utf-8", errors="replace") if e.stderr else ""
            self.queue.put(("error", f"OpenSCAD 실행 실패 (코드 {e.returncode})\n{stderr.strip()}"))
        except Exception as e:
            self.queue.put(("error", f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"))

    def _on_cancel(self) -> None:
        self.cancel_flag.set()
        self.status_var.set("중단 요청됨...")

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self.queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    _, i, total, sym, name = msg
                    self.progress.configure(value=i)
                    self.status_var.set(f"생성 중... {i} / {total}   ({sym} / {name})")
                elif kind == "done":
                    _, n_done, n_total, cancelled, out_dir = msg
                    self.btn_generate.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    if cancelled:
                        self.status_var.set(f"중단됨 — {n_done}개 생성 후 정지")
                    else:
                        self.status_var.set(f"완료 — {n_done}개 STL 파일 생성됨")
                    if self.var_play_sound.get():
                        play_done_sound()
                    if not cancelled and self.var_auto_open.get():
                        open_folder(Path(out_dir))
                elif kind == "error":
                    _, text = msg
                    self.btn_generate.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    self.status_var.set("오류 발생")
                    messagebox.showerror("오류", text, parent=self.root)
        except Empty:
            pass
        self.root.after(120, self._poll_queue)

    # ----- config -----

    def _collect_config(self) -> dict:
        return {
            "openscad_path": self.var_openscad.get(),
            "out_dir": self.var_out_dir.get(),
            "auto_open": bool(self.var_auto_open.get()),
            "play_sound": bool(self.var_play_sound.get()),
            "params": asdict(TileParams(
                font_family=self.var_font_family.get(),
                font_style=self.var_font_style.get(),
                text_thicken=float(self.var_text_thicken.get()),
                text_height=float(self.var_text_height.get()),
                symbol_size=float(self.var_symbol_size.get()),
                name_size=float(self.var_name_size.get()),
                number_size=float(self.var_number_size.get()),
                atomic_size=float(self.var_atomic_size.get()),
                tile_size=float(self.var_tile_size.get()),
                base_thickness=float(self.var_base_thickness.get()),
                fit_clearance=float(self.var_fit_clearance.get()),
            )),
            "selected_numbers": sorted(self.pt.selected),
        }

    def _apply_config(self, data: dict) -> None:
        if "openscad_path" in data: self.var_openscad.set(data["openscad_path"])
        if "out_dir" in data: self.var_out_dir.set(data["out_dir"])
        if "auto_open" in data: self.var_auto_open.set(bool(data["auto_open"]))
        if "play_sound" in data: self.var_play_sound.set(bool(data["play_sound"]))
        p = data.get("params", {})
        for key, var in [
            ("font_family", self.var_font_family),
            ("font_style", self.var_font_style),
            ("text_thicken", self.var_text_thicken),
            ("text_height", self.var_text_height),
            ("symbol_size", self.var_symbol_size),
            ("name_size", self.var_name_size),
            ("number_size", self.var_number_size),
            ("atomic_size", self.var_atomic_size),
            ("tile_size", self.var_tile_size),
            ("base_thickness", self.var_base_thickness),
            ("fit_clearance", self.var_fit_clearance),
        ]:
            if key in p:
                try:
                    var.set(p[key])
                except Exception:
                    pass
        family = self.var_font_family.get()
        for display, fam in self.font_map.items():
            if fam == family:
                self.cb_font.set(display)
                break
        if "selected_numbers" in data:
            self.pt.set_selected(data["selected_numbers"])

    def _on_close(self) -> None:
        try:
            save_config(self._collect_config())
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
