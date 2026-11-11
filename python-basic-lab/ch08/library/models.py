"""도서관의 데이터를 나타내는 클래스와 날짜 표시 함수.

다른 모듈을 가져오지 않는다. 패키지 안에서 가장 아래에 있는 모듈이다.
"""

from dataclasses import dataclass
from datetime import date

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


def format_date(d: date) -> str:
    """날짜를 '2026-11-14(토)' 모양의 문자열로 돌려준다."""
    return f"{d.strftime('%Y-%m-%d')}({WEEKDAYS[d.weekday()]})"


@dataclass(frozen=True)
class Book:
    """도서 한 권. 도서관에 등록된 뒤에는 바뀌지 않는다."""

    code: str
    title: str

    def can_borrow(self) -> bool:
        """관외 대출을 할 수 있으면 True를 돌려준다."""
        return True

    def __str__(self):
        return f"'{self.title}'"


class ReferenceBook(Book):
    """참고 도서(사전 등). 도서관 안에서만 볼 수 있고 대출할 수 없다."""

    def can_borrow(self) -> bool:
        return False


@dataclass
class Loan:
    """대출 한 건."""

    book: Book
    who: str
    due: date

    def overdue_days(self, today: date) -> int:
        """반납 기한에서 today까지 며칠 지났는지 돌려준다. 기한 당일까지는 0이다."""
        return max((today - self.due).days, 0)

    def line(self, today: date) -> str:
        """'B01 파이썬 첫걸음 | 철수 | 기한 2026-11-14(토)' 모양의 한 줄을 돌려준다.

        연체되었으면 끝에 ' | N일 연체'를 붙인다.
        """
        text = f"{self.book.code} {self.book.title} | {self.who} | 기한 {format_date(self.due)}"
        days_over = self.overdue_days(today)
        if days_over > 0:
            text += f" | {days_over}일 연체"
        return text
