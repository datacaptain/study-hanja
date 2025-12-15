# 한자 학습 (Making Hanja)

전국한자능력검정시험 대비를 위한 한자 학습 데스크톱 애플리케이션입니다.

## 기술 스택

- **Desktop App**: Python Flet
- **Database**: SQLite3
- **PDF Generation**: ReportLab

## 기능

- 📚 **한자 목록**: 급수별 한자 검색 및 조회 (5,978개)
- 🎴 **플래시카드**: 카드 형식으로 한자 암기
- ❓ **퀴즈**: 4지선다 퀴즈로 학습 확인
- ✏️ **쓰기 연습**: PDF 다운로드 (10개 한자 × 10번 쓰기)

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화

```bash
python init_db.py
```

### 4. 앱 실행

```bash
python desktop_app.py
```

## 프로젝트 구조

```
making-hanja/
├── desktop_app.py          # Flet 데스크톱 앱
├── init_db.py              # DB 초기화 스크립트
├── making_hanja.sqlite3    # SQLite 데이터베이스
├── hanja.csv               # 한자 데이터
├── requirements.txt        # Python 의존성
└── README.md
```

## 실행파일 빌드

각 플랫폼에서 빌드 스크립트를 실행하면 해당 플랫폼용 실행파일이 생성됩니다.

```bash
# 빌드 의존성 설치
pip install pyinstaller

# 빌드 실행
python build.py
```

### 빌드 결과물
| 플랫폼 | 결과물 |
|--------|--------|
| macOS | `dist/한자학습.app` |
| Windows | `dist/한자학습.exe` |
| Linux | `dist/한자학습` |

> ⚠️ 크로스 컴파일은 지원되지 않습니다. 각 플랫폼에서 직접 빌드해야 합니다.

## 급수 체계

8급 → 7급Ⅱ → 7급 → 6급Ⅱ → 6급 → 5급Ⅱ → 5급 → 4급Ⅱ → 4급 → 3급Ⅱ → 3급 → 2급 → 1급 → 특급Ⅱ → 특급
