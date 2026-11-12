"""가계부 파일을 읽고 요약 파일을 쓰는 함수.

어느 파일을 읽고 쓸지는 정하지 않는다. 경로는 호출하는 쪽(cli)이 넘겨준다.
"""

import csv
from datetime import date
from pathlib import Path

from ledger.models import Summary, Transaction

FIELDNAMES = ["date", "kind", "category", "memo", "amount"]


class DataFileError(Exception):
    """입력 파일의 내용이 형식에 맞지 않는다. problems에 문제 목록을 담는다."""

    def __init__(self, path: Path, problems: list[str]):
        super().__init__(f"{path.name}: 형식 오류 {len(problems)}건")
        self.path = path
        self.problems = problems


def parse_date(text: str) -> date:
    """'2026-10-05' 모양의 문자열을 date로 바꾼다. 아니면 ValueError를 일으킨다."""
    try:
        day = date.fromisoformat(text)
    except ValueError:
        day = None
    if day is None or day.isoformat() != text:
        raise ValueError(f"날짜가 'YYYY-MM-DD' 모양이 아닙니다: {text!r}")
    return day


def parse_amount(text: str) -> int:
    """'12000'이나 '12,000'을 정수로 바꾼다. 형식에 맞지 않으면 ValueError를 일으킨다.

    쉼표는 천 단위 자리에만 올 수 있다. 앞에 '-'가 붙은 음수도 정수로 바꾼다.
    금액이 1 이상인지는 Transaction이 검사한다.
    """
    if not text:
        raise ValueError("금액이 비어 있습니다")
    negative = text.startswith("-")
    body = text[1:] if negative else text
    digits = body.replace(",", "")
    if not digits.isdecimal():
        raise ValueError(f"금액이 정수가 아닙니다: {text!r}")
    amount = int(digits)
    if "," in body and f"{amount:,}" != body:
        raise ValueError(f"금액의 쉼표 위치가 잘못되었습니다: {text!r}")
    return -amount if negative else amount


def parse_row(row: dict) -> Transaction:
    """DictReader가 읽은 한 줄을 Transaction으로 바꾼다.

    값이 형식이나 규칙에 맞지 않으면 ValueError를 일으킨다.
    """
    if None in row:
        raise ValueError("칸이 너무 많습니다")
    values = {}
    for name in FIELDNAMES:
        values[name] = (row[name] or "").strip()
    return Transaction(
        day=parse_date(values["date"]),
        kind=values["kind"],
        category=values["category"],
        memo=values["memo"],
        amount=parse_amount(values["amount"]),
    )


def load_transactions(path: Path) -> list[Transaction]:
    """CSV 파일에서 거래 목록을 읽어 파일에 적힌 순서대로 돌려준다.

    첫 줄만 있고 거래가 없으면 빈 리스트를 돌려준다.
    파일이 없으면 FileNotFoundError를 그대로 보낸다.
    빈 파일, UTF-8이 아닌 파일, 따옴표가 맞지 않는 등 CSV 형식이 깨진 파일,
    첫 줄이 다른 파일이면 DataFileError를 일으킨다.
    값이 맞지 않는 줄이 있으면 문제를 모두 모아 DataFileError 하나로 알린다.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        try:
            fieldnames = reader.fieldnames
            rows = []
            for row in reader:
                rows.append((reader.line_num, row))
        except UnicodeDecodeError as e:
            raise DataFileError(
                path,
                [
                    "UTF-8로 읽을 수 없습니다. 엑셀에서는 'CSV UTF-8' 형식으로 저장하세요"
                ],
            ) from e
        except csv.Error as e:
            # 오류가 난 레코드는 마지막으로 다 읽은 줄(line_num)의 다음 줄에서 시작한다.
            raise DataFileError(
                path,
                [
                    f"{reader.line_num + 1}번째 줄 근처: CSV 형식이 깨졌습니다. "
                    "큰따옴표의 짝을 확인하세요"
                ],
            ) from e

    if fieldnames is None:
        raise DataFileError(path, ["파일이 비어 있습니다"])
    if fieldnames != FIELDNAMES:
        raise DataFileError(path, [f"첫 줄은 {','.join(FIELDNAMES)}여야 합니다"])

    transactions = []
    problems = []
    for line_no, row in rows:
        try:
            transactions.append(parse_row(row))
        except ValueError as e:
            problems.append(f"{line_no}번째 줄: {e}")
    if problems:
        raise DataFileError(path, problems)
    return transactions


def write_summary(summary: Summary, path: Path) -> None:
    """지출 분류별 합계를 엑셀에서 열 수 있는 CSV 파일로 저장한다.

    열은 분류, 금액, 비율(%)이고 금액이 큰 순이다. 마지막 줄은 합계다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["분류", "금액", "비율(%)"])
        for category, amount in summary.expense_by_category:
            writer.writerow([category, amount, f"{summary.share(amount):.1f}"])
        writer.writerow(
            ["합계", summary.expense, f"{summary.share(summary.expense):.1f}"]
        )
