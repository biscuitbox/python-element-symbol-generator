# 원소 타일 생성기 (Element Tile Generator)

중학교 화학 수업용 **원소 타일**(가로·세로 약 8cm 정사각 플레이트)을
3D 프린터로 한꺼번에 출력할 수 있도록 STL 파일을 생성해 주는 도구입니다.
주기율표 GUI에서 원소를 클릭하기만 하면 끝납니다.

타일 한 장에는 **원자번호 / 원소 기호 / 한글 이름 / 원자량**이 양각으로
새겨지고, 좌우 슬롯에 끼움쇠를 꽂아 옆 타일과 결합할 수 있습니다.

> 비개발자(선생님·학생) 대상 단계별 안내는 **[`사용설명서.md`](사용설명서.md)**,
> 프로젝트 전체 맥락과 AI 협업 기록은 **[`CLAUDE.md`](CLAUDE.md)** 를 참고하세요.

---

## 빠른 시작 (GUI)

1. **Python 3.x**, **OpenSCAD**, **한글 폰트(나눔고딕 등)**를 설치합니다.
2. 이 폴더의 **`타일생성기.bat`** 파일을 더블클릭합니다.
3. GUI 창에서
   - **원소 선택** 탭에서 주기율표를 클릭해 원소 고르기
   - **글자 디자인 / 인쇄 설정 / 출력 설정** 탭에서 옵션 조정
   - 하단의 **"🧪 STL 생성 시작"** 버튼 누르기
4. 작업이 끝나면 결과 폴더가 자동으로 열립니다. 슬라이서로 열어 출력하세요.

검은 명령창(터미널)을 만질 필요가 없습니다.

---

## 주요 기능

- **주기율표 GUI** — 1번 수소부터 118번 오가네손까지 클릭으로 선택
- **카테고리별 색상** — 알칼리/할로젠/비활성기체 등 10개 그룹 색 구분
  (란타넘족·악티늄족 별도 표시)
- **CSV 입력 모드** — 직접 만든 표 파일도 사용 가능
- **글자 디자인** — 4개 텍스트 각각의 mm 크기, 폰트, 굵기, 추가 두껍게,
  새김 깊이를 모두 조정
- **상용 가능 한글 폰트만** 자동 필터해 드롭다운에 표시
- **인쇄 설정** — 타일 크기·두께, 끼움 여유(`fit_clearance`)
- **OpenSCAD 자동 탐지** + **결과 폴더 자동 열기** + **완료 알림음**
- **프리셋 저장·불러오기** (JSON) + **마지막 사용 설정 자동 기억**
- **백그라운드 작업 + 진행률 + 중단** — 큰 일괄 생성 중에도 GUI 안 멈춤
- **중학교 권장 15종 빠른 선택** 버튼

---

## 폴더 구조

| 파일 | 설명 |
|---|---|
| `타일생성기.bat` | **더블클릭으로 GUI 실행** (비개발자용 진입점) |
| `gui.py` | tkinter 기반 GUI 본체 |
| `generate_tiles.py` | OpenSCAD 호출 + STL 생성 핵심 로직 (CLI도 지원) |
| `periodic_table.py` | 118개 원소 데이터(한국화학회 명명) + 카테고리 + 좌표 |
| `element_tiles.scad` | 타일·끼움쇠의 3D 모양을 정의한 OpenSCAD 설계도 |
| `samples/elements_sample.csv` | CSV 입력 샘플 |
| `사용설명서.md` | 비개발자용 단계별 한글 안내 |
| `CLAUDE.md` | 프로젝트 전체 안내 + AI 협업 기록 |

---

## 사전 준비

### 1. Python 3.x
[python.org](https://www.python.org/downloads/) 에서 설치.
설치 시 **"Add Python to PATH"** 체크 필수. tkinter는 기본 포함이라
별도 설치가 필요 없습니다.

### 2. OpenSCAD
[openscad.org](https://openscad.org/downloads.html) 에서 설치.
GUI가 자동으로 경로를 찾아주며, 못 찾으면 설정 탭에서 직접 지정할 수 있습니다.

### 3. 한글 폰트 (최소 1개)
한글 글자가 또렷이 새겨지려면 다음 중 **하나 이상**이 시스템에 깔려 있어야 합니다.
모두 상업적 이용이 가능한 무료 폰트입니다.

- 나눔고딕 / 나눔명조 / 나눔스퀘어 (Naver)
- 본고딕 (Noto Sans KR, Google)
- 프리텐다드 (Pretendard)
- 에스코어 드림, 카페24 시리즈, 배민 한나/도현/주아 등

가장 무난한 선택은 **나눔고딕**입니다.

---

## CLI 사용법 (개발자·자동화용)

GUI 없이 명령줄에서도 실행할 수 있습니다.

### CSV로 일괄 생성

**Windows (PowerShell):**
```powershell
python generate_tiles.py samples\elements_sample.csv `
  --out out `
  --openscad "C:\Program Files\OpenSCAD\openscad.exe"
```

**macOS / Linux:**
```bash
python3 generate_tiles.py samples/elements_sample.csv --out out
```

CSV 필수 컬럼(한글/영문 모두 허용):
`symbol`/`기호`, `name`/`이름`, `number`/`원자량`, `atomic_number`/`원자번호`

### 원소 1개만 출력 (한글 포함 시)

한글을 OpenSCAD `-D` 인자로 직접 넘기면 Windows 코드페이지 문제로
글자가 두부(☒)로 깨집니다. **반드시 UTF-8 wrapper SCAD**를 만들어 넘기세요.

```scad
// my_tile.scad (UTF-8로 저장)
include <element_tiles.scad>
symbol = "Te";
name = "텔루륨";
number = "127.60";
atomic_number = "52";
```

```powershell
& "C:\Program Files\OpenSCAD\openscad.exe" -o Te.stl my_tile.scad
```

영문/숫자만 들어가면 `-D` 방식도 가능합니다:
```bash
openscad -o H.stl -D 'symbol="H"' -D 'name="Hydrogen"' \
  -D 'number="1.008"' -D 'atomic_number="1"' element_tiles.scad
```

### 끼움쇠(커넥터)만 출력
```bash
openscad -o connector.stl -D "show_tile=false" -D "show_connector=true" element_tiles.scad
```

---

## 알려진 함정 (Windows + 한글)

이 프로젝트가 단순해 보여도 **Windows + 한글 + OpenSCAD** 조합에 두 가지
함정이 있어, 이를 우회하는 것이 코드의 핵심입니다.

1. **한글이 두부(☒)로 깨짐** — OpenSCAD CLI에 한글을 `-D`로 넘기면 CP949로
   잘못 해석됩니다. → 도구가 **UTF-8 SCAD 파일**을 만들어 넘기는 방식으로
   우회합니다.
2. **한글 폴더 경로에서 `include` 실패** — 경로에 한글이 있으면 OpenSCAD가
   파일을 못 엽니다. → 도구가 매 실행마다 **영문만 들어 있는 임시 폴더**에
   템플릿을 복사해 그 안에서 실행합니다.

자세한 내용은 [CLAUDE.md §8](CLAUDE.md) 참고.

---

## 출력 권장 설정 (수업용)

- 텍스트 높이 `0.8~1.0` mm — 가독성 강화
- 모서리 라운드 약간 키우기 — 손베임 방지
- `fit_clearance` `0.2~0.3` — 시험 출력해서 결합 강도 맞추기
- 원소군(금속/비금속/준금속)별로 다른 색 필라멘트 — 학생 분류 활동에 유용

---

## 라이선스

- **이 프로젝트의 코드**: (사용자가 원하는 라이선스를 여기에 명시)
- **OpenSCAD**: GPLv2 (별도 설치된 OpenSCAD를 호출만 함)
- **권장 한글 폰트**: 모두 상업적 이용이 가능한 무료 폰트만 GUI에 노출됨.
  단, 폰트 자체를 재배포할 경우 각 폰트의 라이선스 조건을 별도 확인하세요.

---

## 크레딧

이 프로젝트는 **Claude (Anthropic)** 와 협업해 제작되었습니다.
사용자가 의뢰·결정·검수를 맡고, AI가 코드 작성·디버깅·문서화를 담당했습니다.
협업 단계별 기록은 [`CLAUDE.md`](CLAUDE.md) §9 를 참고하세요.
