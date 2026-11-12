"""가계부 요약 프로그램의 시작 파일. python main.py 가계부파일.csv로 실행한다."""

import sys

try:
    from ledger.cli import main
except ModuleNotFoundError as e:
    if e.name != "rich":
        raise
    print("rich 패키지를 찾을 수 없습니다.", file=sys.stderr)
    print(f"실행한 파이썬: {sys.executable}", file=sys.stderr)
    print(
        "가상환경을 활성화했는지 확인하고, "
        "python -m pip install -r requirements.txt로 설치하세요.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
