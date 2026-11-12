"""명령행에서 가계부 파일을 받아 요약을 보여 주고 저장하는 화면 쪽 코드.

프로그램의 시작점인 main()이 있다. rich를 가져오는 모듈은 이것 하나뿐이다.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from ledger.core import summarize
from ledger.models import Summary
from ledger.storage import DataFileError, load_transactions, write_summary

USAGE = "사용법: python main.py 가계부파일.csv"
MAX_PROBLEMS = 10  # 형식 오류를 화면에 몇 건까지 보여 줄지

console = Console()
error_console = Console(stderr=True)


def won(amount: int) -> str:
    """금액을 '1,234원' 모양으로 돌려준다."""
    return f"{amount:,}원"


def summary_path(path: Path) -> Path:
    """입력 파일 옆에 저장할 요약 파일의 경로를 돌려준다.

    samples/2026-10.csv → samples/2026-10_summary.csv
    """
    return path.with_name(f"{path.stem}_summary.csv")


def category_table(summary: Summary) -> Table:
    """지출 분류별 합계 표를 만든다. 출력은 하지 않는다."""
    table = Table(title="지출 분류별 합계")
    table.add_column("분류")
    table.add_column("금액", justify="right")
    table.add_column("비율", justify="right")
    for category, amount in summary.expense_by_category:
        table.add_row(escape(category), won(amount), f"{summary.share(amount):.1f}%")
    table.add_section()
    table.add_row(
        "합계",
        won(summary.expense),
        f"{summary.share(summary.expense):.1f}%",
        style="bold",
    )
    return table


def print_problems(error: DataFileError) -> None:
    """형식 오류를 표준 오류로 출력한다.

    MAX_PROBLEMS건이 넘으면 나머지는 개수만 알린다.
    """
    error_console.print(escape(str(error)), style="bold red")
    for problem in error.problems[:MAX_PROBLEMS]:
        error_console.print(f"  {escape(problem)}", style="red")
    rest = len(error.problems) - MAX_PROBLEMS
    if rest > 0:
        error_console.print(f"  ... 외 {rest}건", style="red")


def main() -> None:
    """명령행 인자로 받은 가계부 파일을 요약해 보여 주고, 요약 파일을 저장한다."""
    if len(sys.argv) != 2:
        print(USAGE, file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])

    try:
        transactions = load_transactions(path)
    except FileNotFoundError:
        error_console.print(f"파일이 없습니다: {escape(str(path))}", style="red")
        sys.exit(1)
    except DataFileError as e:
        print_problems(e)
        error_console.print(
            "파일을 고친 뒤 다시 실행하세요. 요약 파일은 만들지 않았습니다."
        )
        sys.exit(1)

    if not transactions:
        console.print(f"거래 내역이 없습니다: {escape(str(path))}")
        return

    summary = summarize(transactions)
    console.print(f"가계부 요약: {escape(path.name)}", style="bold")
    console.print(
        f"기간: {summary.first_day} ~ {summary.last_day} (거래 {summary.count}건)"
    )
    console.print(f"수입: {won(summary.income)}")
    console.print(f"지출: {won(summary.expense)}")
    balance_style = "red" if summary.balance < 0 else None
    console.print(f"잔액: {won(summary.balance)}", style=balance_style)
    console.print(category_table(summary))

    out_path = summary_path(path)
    write_summary(summary, out_path)
    console.print(f"요약을 저장했습니다: {escape(str(out_path))}")
