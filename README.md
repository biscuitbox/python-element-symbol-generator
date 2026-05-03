## 원소기호 타일 생성기

### 1) 한글 폰트(나눔) 적용
- `element_tiles.scad`에서 `font_name = "NanumGothic:style=Regular"`로 설정되어 있습니다.
- 시스템에 나눔고딕이 설치되어 있어야 합니다.

### 2) 표 파일로 여러 원소 한 번에 STL 생성 (권장)
`generate_tiles.py`를 사용하면 `.csv` 또는 `.tsv`의 각 행마다 STL이 생성됩니다.
한글이 포함된 이름도 안전하게 처리됩니다.

필수 컬럼(한글/영문 모두 허용):
- `symbol` 또는 `기호`
- `name` 또는 `이름`
- `number` 또는 `원자량`
- `atomic_number` 또는 `원자번호`

샘플 파일: `samples/elements_sample.csv`

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

> Windows에서 OpenSCAD를 PATH에 추가했다면 `--openscad` 옵션은 생략 가능합니다.

### 3) 한 개만 출력하기
한글이 포함될 경우 OpenSCAD CLI의 `-D` 인자로 직접 넘기면
Windows 코드페이지 문제로 한글이 두부(☒)로 깨집니다.
대신 임시 wrapper SCAD를 만들어 OpenSCAD에 넘기세요. 예시:

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

영문/숫자만 들어가는 원소(H, He, C, …)는 `-D` 방식도 사용 가능합니다:
```bash
openscad -o H.stl -D 'symbol="H"' -D 'name="Hydrogen"' \
  -D 'number="1.008"' -D 'atomic_number="1"' element_tiles.scad
```

### 4) 커넥터만 출력하려면
```bash
openscad -o connector.stl -D "show_tile=false" -D "show_connector=true" element_tiles.scad
```

### 5) 중학생 수업용 추가 권장사항
- 텍스트 높이를 `0.8~1.0`으로 올려 가독성 강화
- 모서리 라운드를 조금 키워 손베임 방지
- `fit_clearance`를 0.2~0.3까지 시험 출력해서 결합 강도 맞추기
- 원소군(금속/비금속/준금속)별 색상 필라멘트 규칙 정하기
