#!/usr/bin/env python3
"""
빌드 스크립트 - 한자 학습 데스크톱 앱
각 플랫폼에서 실행하면 해당 플랫폼용 실행파일이 생성됩니다.
"""
import subprocess
import sys
import platform

def main():
    os_name = platform.system()
    print(f"빌드 시작: {os_name}")
    
    # 빌드 명령어
    cmd = [
        sys.executable, "-m", "flet", "pack",
        "desktop_app.py",
        "--name", "한자학습",
        "--add-data", f"making_hanja.sqlite3{':' if os_name != 'Windows' else ';'}.",
        "--add-data", f"hanja.csv{':' if os_name != 'Windows' else ';'}.",
    ]
    
    print(f"실행 명령어: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 빌드 완료!")
        print("실행파일 위치: dist/")
        if os_name == "Darwin":
            print("  - 한자학습.app (macOS 앱 번들)")
        elif os_name == "Windows":
            print("  - 한자학습.exe")
        else:
            print("  - 한자학습")
    else:
        print("\n❌ 빌드 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
