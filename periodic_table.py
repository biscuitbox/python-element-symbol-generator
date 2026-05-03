"""Periodic table data for the GUI.

Each entry: (atomic_number, symbol, korean_name, atomic_weight, category, row, col)

`row` / `col` follow the standard 18-column periodic table layout, with
lanthanides on row 8 and actinides on row 9 (separated by a visual gap).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PTEntry:
    number: int
    symbol: str
    name: str
    weight: str
    category: str
    row: int
    col: int


CATEGORY_INFO: dict[str, tuple[str, str]] = {
    # key:               (Korean label,        cell color)
    "alkali":            ("알칼리 금속",        "#FF8B8B"),
    "alkaline":          ("알칼리 토금속",      "#FFB870"),
    "transition":        ("전이 금속",          "#FFD960"),
    "post_transition":   ("전이 후 금속",       "#A8D8B0"),
    "metalloid":         ("준금속",             "#7FC4C4"),
    "nonmetal":          ("비금속",             "#80BCE0"),
    "halogen":           ("할로젠",             "#F58F60"),
    "noble":             ("비활성 기체",        "#C898E0"),
    "lanthanide":        ("란타넘족",           "#FFB0E0"),
    "actinide":          ("악티늄족",           "#FF9090"),
}


_RAW: list[tuple] = [
    (1,  "H",  "수소",       "1.008",  "nonmetal",        1, 1),
    (2,  "He", "헬륨",       "4.003",  "noble",           1, 18),
    (3,  "Li", "리튬",       "6.94",   "alkali",          2, 1),
    (4,  "Be", "베릴륨",     "9.012",  "alkaline",        2, 2),
    (5,  "B",  "붕소",       "10.81",  "metalloid",       2, 13),
    (6,  "C",  "탄소",       "12.01",  "nonmetal",        2, 14),
    (7,  "N",  "질소",       "14.01",  "nonmetal",        2, 15),
    (8,  "O",  "산소",       "16.00",  "nonmetal",        2, 16),
    (9,  "F",  "플루오린",   "19.00",  "halogen",         2, 17),
    (10, "Ne", "네온",       "20.18",  "noble",           2, 18),
    (11, "Na", "나트륨",     "22.99",  "alkali",          3, 1),
    (12, "Mg", "마그네슘",   "24.31",  "alkaline",        3, 2),
    (13, "Al", "알루미늄",   "26.98",  "post_transition", 3, 13),
    (14, "Si", "규소",       "28.09",  "metalloid",       3, 14),
    (15, "P",  "인",         "30.97",  "nonmetal",        3, 15),
    (16, "S",  "황",         "32.06",  "nonmetal",        3, 16),
    (17, "Cl", "염소",       "35.45",  "halogen",         3, 17),
    (18, "Ar", "아르곤",     "39.95",  "noble",           3, 18),
    (19, "K",  "칼륨",       "39.10",  "alkali",          4, 1),
    (20, "Ca", "칼슘",       "40.08",  "alkaline",        4, 2),
    (21, "Sc", "스칸듐",     "44.96",  "transition",      4, 3),
    (22, "Ti", "타이타늄",   "47.87",  "transition",      4, 4),
    (23, "V",  "바나듐",     "50.94",  "transition",      4, 5),
    (24, "Cr", "크로뮴",     "52.00",  "transition",      4, 6),
    (25, "Mn", "망가니즈",   "54.94",  "transition",      4, 7),
    (26, "Fe", "철",         "55.85",  "transition",      4, 8),
    (27, "Co", "코발트",     "58.93",  "transition",      4, 9),
    (28, "Ni", "니켈",       "58.69",  "transition",      4, 10),
    (29, "Cu", "구리",       "63.55",  "transition",      4, 11),
    (30, "Zn", "아연",       "65.38",  "transition",      4, 12),
    (31, "Ga", "갈륨",       "69.72",  "post_transition", 4, 13),
    (32, "Ge", "저마늄",     "72.63",  "metalloid",       4, 14),
    (33, "As", "비소",       "74.92",  "metalloid",       4, 15),
    (34, "Se", "셀레늄",     "78.97",  "nonmetal",        4, 16),
    (35, "Br", "브로민",     "79.90",  "halogen",         4, 17),
    (36, "Kr", "크립톤",     "83.80",  "noble",           4, 18),
    (37, "Rb", "루비듐",     "85.47",  "alkali",          5, 1),
    (38, "Sr", "스트론튬",   "87.62",  "alkaline",        5, 2),
    (39, "Y",  "이트륨",     "88.91",  "transition",      5, 3),
    (40, "Zr", "지르코늄",   "91.22",  "transition",      5, 4),
    (41, "Nb", "나이오븀",   "92.91",  "transition",      5, 5),
    (42, "Mo", "몰리브데넘", "95.95",  "transition",      5, 6),
    (43, "Tc", "테크네튬",   "98",     "transition",      5, 7),
    (44, "Ru", "루테늄",     "101.1",  "transition",      5, 8),
    (45, "Rh", "로듐",       "102.9",  "transition",      5, 9),
    (46, "Pd", "팔라듐",     "106.4",  "transition",      5, 10),
    (47, "Ag", "은",         "107.9",  "transition",      5, 11),
    (48, "Cd", "카드뮴",     "112.4",  "transition",      5, 12),
    (49, "In", "인듐",       "114.8",  "post_transition", 5, 13),
    (50, "Sn", "주석",       "118.7",  "post_transition", 5, 14),
    (51, "Sb", "안티모니",   "121.8",  "metalloid",       5, 15),
    (52, "Te", "텔루륨",     "127.6",  "metalloid",       5, 16),
    (53, "I",  "아이오딘",   "126.9",  "halogen",         5, 17),
    (54, "Xe", "제논",       "131.3",  "noble",           5, 18),
    (55, "Cs", "세슘",       "132.9",  "alkali",          6, 1),
    (56, "Ba", "바륨",       "137.3",  "alkaline",        6, 2),
    (57, "La", "란타넘",       "138.9",  "lanthanide",      8, 3),
    (58, "Ce", "세륨",         "140.1",  "lanthanide",      8, 4),
    (59, "Pr", "프라세오디뮴", "140.9",  "lanthanide",      8, 5),
    (60, "Nd", "네오디뮴",     "144.2",  "lanthanide",      8, 6),
    (61, "Pm", "프로메튬",     "145",    "lanthanide",      8, 7),
    (62, "Sm", "사마륨",       "150.4",  "lanthanide",      8, 8),
    (63, "Eu", "유로퓸",       "152.0",  "lanthanide",      8, 9),
    (64, "Gd", "가돌리늄",     "157.3",  "lanthanide",      8, 10),
    (65, "Tb", "터븀",         "158.9",  "lanthanide",      8, 11),
    (66, "Dy", "디스프로슘",   "162.5",  "lanthanide",      8, 12),
    (67, "Ho", "홀뮴",         "164.9",  "lanthanide",      8, 13),
    (68, "Er", "어븀",         "167.3",  "lanthanide",      8, 14),
    (69, "Tm", "툴륨",         "168.9",  "lanthanide",      8, 15),
    (70, "Yb", "이터븀",       "173.0",  "lanthanide",      8, 16),
    (71, "Lu", "루테튬",       "175.0",  "lanthanide",      8, 17),
    (72, "Hf", "하프늄",       "178.5",  "transition",      6, 4),
    (73, "Ta", "탄탈럼",       "180.9",  "transition",      6, 5),
    (74, "W",  "텅스텐",       "183.8",  "transition",      6, 6),
    (75, "Re", "레늄",         "186.2",  "transition",      6, 7),
    (76, "Os", "오스뮴",       "190.2",  "transition",      6, 8),
    (77, "Ir", "이리듐",       "192.2",  "transition",      6, 9),
    (78, "Pt", "백금",         "195.1",  "transition",      6, 10),
    (79, "Au", "금",           "197.0",  "transition",      6, 11),
    (80, "Hg", "수은",         "200.6",  "transition",      6, 12),
    (81, "Tl", "탈륨",         "204.4",  "post_transition", 6, 13),
    (82, "Pb", "납",           "207.2",  "post_transition", 6, 14),
    (83, "Bi", "비스무트",     "209.0",  "post_transition", 6, 15),
    (84, "Po", "폴로늄",       "209",    "post_transition", 6, 16),
    (85, "At", "아스타틴",     "210",    "halogen",         6, 17),
    (86, "Rn", "라돈",         "222",    "noble",           6, 18),
    (87, "Fr", "프랑슘",       "223",    "alkali",          7, 1),
    (88, "Ra", "라듐",         "226",    "alkaline",        7, 2),
    (89, "Ac", "악티늄",         "227",    "actinide",        9, 3),
    (90, "Th", "토륨",           "232.0",  "actinide",        9, 4),
    (91, "Pa", "프로트악티늄",   "231.0",  "actinide",        9, 5),
    (92, "U",  "우라늄",         "238.0",  "actinide",        9, 6),
    (93, "Np", "넵투늄",         "237",    "actinide",        9, 7),
    (94, "Pu", "플루토늄",       "244",    "actinide",        9, 8),
    (95, "Am", "아메리슘",       "243",    "actinide",        9, 9),
    (96, "Cm", "퀴륨",           "247",    "actinide",        9, 10),
    (97, "Bk", "버클륨",         "247",    "actinide",        9, 11),
    (98, "Cf", "캘리포늄",       "251",    "actinide",        9, 12),
    (99, "Es", "아인슈타이늄",   "252",    "actinide",        9, 13),
    (100, "Fm", "페르뮴",        "257",    "actinide",        9, 14),
    (101, "Md", "멘델레븀",      "258",    "actinide",        9, 15),
    (102, "No", "노벨륨",        "259",    "actinide",        9, 16),
    (103, "Lr", "로렌슘",        "266",    "actinide",        9, 17),
    (104, "Rf", "러더포듐",      "267",    "transition",      7, 4),
    (105, "Db", "두브늄",        "268",    "transition",      7, 5),
    (106, "Sg", "시보귬",        "269",    "transition",      7, 6),
    (107, "Bh", "보륨",          "270",    "transition",      7, 7),
    (108, "Hs", "하슘",          "277",    "transition",      7, 8),
    (109, "Mt", "마이트너륨",    "278",    "transition",      7, 9),
    (110, "Ds", "다름슈타튬",    "281",    "transition",      7, 10),
    (111, "Rg", "뢴트게늄",      "282",    "transition",      7, 11),
    (112, "Cn", "코페르니슘",    "285",    "transition",      7, 12),
    (113, "Nh", "니호늄",        "286",    "post_transition", 7, 13),
    (114, "Fl", "플레로븀",      "289",    "post_transition", 7, 14),
    (115, "Mc", "모스코븀",      "290",    "post_transition", 7, 15),
    (116, "Lv", "리버모륨",      "293",    "post_transition", 7, 16),
    (117, "Ts", "테네신",        "294",    "halogen",         7, 17),
    (118, "Og", "오가네손",      "294",    "noble",           7, 18),
]


ELEMENTS: list[PTEntry] = [PTEntry(*row) for row in _RAW]
BY_NUMBER: dict[int, PTEntry] = {e.number: e for e in ELEMENTS}
BY_SYMBOL: dict[str, PTEntry] = {e.symbol: e for e in ELEMENTS}

# Markers shown in (period 6, group 3) and (period 7, group 3) cells —
# these point the user to the lanthanide/actinide rows below.
PLACEHOLDERS: list[tuple[int, int, str, str]] = [
    (6, 3, "57-71",  "lanthanide"),
    (7, 3, "89-103", "actinide"),
]
