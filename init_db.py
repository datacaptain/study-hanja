"""
Database initialization script for Hanja Learning Application.
Creates SQLite database and imports data from hanja.csv.
"""
import csv
import os
import sqlite3
import ast

# Grade order for sorting
GRADE_ORDER = {
    '8급': 1,
    '7급Ⅱ': 2, '7급': 3,
    '6급Ⅱ': 4, '6급': 5,
    '5급Ⅱ': 6, '5급': 7,
    '4급Ⅱ': 8, '4급': 9,
    '3급Ⅱ': 10, '3급': 11,
    '2급': 12,
    '1급': 13,
    '특급Ⅱ': 14, '특급': 15
}

DB_PATH = os.environ.get('MAKING_HANJA_DB_PATH',
                         os.path.join(os.path.dirname(__file__), 'making_hanja.sqlite3'))
CSV_PATH = os.path.join(os.path.dirname(__file__), 'hanja.csv')


def create_tables(conn):
    """Create database tables."""
    cursor = conn.cursor()
    
    # Hanja table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hanja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_sound TEXT NOT NULL,
            level TEXT NOT NULL,
            level_order INTEGER NOT NULL,
            hanja TEXT NOT NULL,
            meaning TEXT NOT NULL,
            radical TEXT,
            strokes INTEGER,
            total_strokes INTEGER
        )
    ''')
    
    # Progress tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            hanja_id INTEGER NOT NULL,
            result TEXT NOT NULL CHECK(result IN ('correct', 'incorrect')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hanja_id) REFERENCES hanja(id)
        )
    ''')
    
    # Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hanja_level ON hanja(level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hanja_sound ON hanja(main_sound)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_client ON progress(client_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_hanja ON progress(hanja_id)')
    
    conn.commit()
    print("테이블 생성 완료")


def parse_meaning(meaning_str):
    """Parse meaning string to readable format."""
    try:
        # The meaning is in format: [[['meaning1', 'meaning2'], ['sound1']], ...]
        data = ast.literal_eval(meaning_str)
        parts = []
        for item in data:
            meanings = item[0]
            sounds = item[1] if len(item) > 1 else []
            meaning_text = ', '.join(meanings)
            if sounds:
                sound_text = '/'.join(sounds)
                parts.append(f"{meaning_text} [{sound_text}]")
            else:
                parts.append(meaning_text)
        return ' | '.join(parts)
    except (ValueError, SyntaxError, IndexError):
        return meaning_str


def import_csv(conn):
    """Import hanja data from CSV file."""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM hanja')
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            level = row['level']
            level_order = GRADE_ORDER.get(level, 99)
            meaning = parse_meaning(row['meaning'])
            
            cursor.execute('''
                INSERT INTO hanja (main_sound, level, level_order, hanja, meaning, radical, strokes, total_strokes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                row['main_sound'],
                level,
                level_order,
                row['hanja'],
                meaning,
                row['radical'],
                int(row['strokes']) if row['strokes'] else None,
                int(row['total_strokes']) if row['total_strokes'] else None
            ])
            count += 1
            
            if count % 500 == 0:
                print(f"{count}개 한자 가져오기 완료...")
    
    conn.commit()
    print(f"총 {count}개 한자 데이터 가져오기 완료")


def main():
    """Initialize database."""
    print(f"데이터베이스 경로: {DB_PATH}")
    print(f"CSV 파일 경로: {CSV_PATH}")
    
    # Create database directory if needed
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        create_tables(conn)
        import_csv(conn)
        
        # Verify
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM hanja')
        total = cursor.fetchone()[0]
        print(f"검증: 데이터베이스에 {total}개의 한자가 저장되었습니다")
        
        cursor.execute('SELECT level, COUNT(*) FROM hanja GROUP BY level ORDER BY level_order')
        print("\n급수별 한자 수:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}개")
            
    finally:
        conn.close()
    
    print("\n데이터베이스 초기화 완료!")


if __name__ == '__main__':
    main()
