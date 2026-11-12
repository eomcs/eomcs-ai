"""samples 폴더의 시험 파일을 읽고 요약해서, 기대한 결과와 같은지 확인한다.

확인하는 것은 storage(읽기와 검사)와 core(계산)의 결과다. 화면 출력(cli)과
저장한 요약 파일은 확인하지 않는다. 코드를 고친 뒤 python check_samples.py로
실행한다. 모두 통과하면 종료 코드 0이다.
"""

import sys
from pathlib import Path

from ledger.core import summarize
from ledger.storage import DataFileError, load_transactions

SAMPLES_DIR = Path(__file__).parent / "samples"

# {시험 파일 이름: 기대하는 결과의 줄}. 숫자는 계산기로 직접 구한 값이다.
EXPECTED = {
    "2026-10.csv": [
        "거래 14건",
        "기간 2026-10-01 ~ 2026-10-31",
        "수입 2835000, 지출 969500, 잔액 1865500",
        "지출 주거 550000",
        "지출 식비 209700",
        "지출 문화 70000",
        "지출 교통 50000",
        "지출 통신 45000",
        "지출 교육 32000",
        "지출 의료 12800",
    ],
    "header_only.csv": ["거래 0건"],
    "empty.csv": ["형식 오류", "파일이 비어 있습니다"],
    "bad_quote.csv": [
        "형식 오류",
        "3번째 줄 근처: CSV 형식이 깨졌습니다. 큰따옴표의 짝을 확인하세요",
    ],
    "broken.csv": [
        "형식 오류",
        "3번째 줄: 날짜가 'YYYY-MM-DD' 모양이 아닙니다: '2026/10/03'",
        "4번째 줄: 구분은 '수입'이나 '지출'이어야 합니다: '지츨'",
        "5번째 줄: 칸이 너무 많습니다",
        "6번째 줄: 분류가 비어 있습니다",
        "7번째 줄: 금액이 정수가 아닙니다: '6만2천원'",
        "8번째 줄: 금액은 1 이상이어야 합니다: -32000",
        "9번째 줄: 금액이 비어 있습니다",
        "10번째 줄: 날짜가 'YYYY-MM-DD' 모양이 아닙니다: '2026-02-30'",
        "11번째 줄: 금액의 쉼표 위치가 잘못되었습니다: '38,00'",
    ],
}


def describe(path: Path) -> list[str]:
    """path를 읽고 요약한 결과를 비교하기 쉬운 문자열의 리스트로 돌려준다."""
    try:
        transactions = load_transactions(path)
    except DataFileError as e:
        return ["형식 오류"] + e.problems
    if not transactions:
        return ["거래 0건"]
    summary = summarize(transactions)
    lines = [
        f"거래 {summary.count}건",
        f"기간 {summary.first_day} ~ {summary.last_day}",
        f"수입 {summary.income}, 지출 {summary.expense}, 잔액 {summary.balance}",
    ]
    for category, amount in summary.expense_by_category:
        lines.append(f"지출 {category} {amount}")
    return lines


def main() -> None:
    failed = 0
    for name, expected in EXPECTED.items():
        actual = describe(SAMPLES_DIR / name)
        if actual == expected:
            print(f"[통과] {name}")
            continue
        failed += 1
        print(f"[실패] {name}")
        for line in expected:
            if line not in actual:
                print(f"  기대했는데 없다: {line}")
        for line in actual:
            if line not in expected:
                print(f"  기대하지 않았는데 있다: {line}")
        if sorted(actual) == sorted(expected):
            print("  줄은 같은데 순서가 다르다")
    print(f"{len(EXPECTED)}개 중 {len(EXPECTED) - failed}개 통과")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
