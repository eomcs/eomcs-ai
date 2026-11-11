"""도서관의 규칙을 담은 Library 클래스.

파일을 모른다. 그래서 csv, json, pathlib과 storage 모듈을 가져오지 않는다.
"""

from collections import defaultdict
from datetime import date, timedelta

# 규칙(2층)은 errors(1층)와 models(0층)만 가져온다. csv, json, pathlib과
# storage, cli를 가져오는 줄이 없다는 것이 "Library는 파일을 모른다"의 증거다.
from library.errors import (
    AlreadyBorrowedError,
    BookNotFoundError,
    NotBorrowableError,
    NotBorrowedError,
)
from library.models import Book, Loan


class Library:
    """도서관. 소장 도서와 대출 기록을 관리한다."""

    LOAN_DAYS = 14
    LATE_FEE_PER_DAY = 100

    def __init__(self, books: list[Book]):
        """books의 도서를 소장한다. 대출 기록은 비어 있는 상태로 시작한다.

        도서 코드가 겹치는 도서가 있으면 ValueError를 일으킨다.
        """
        self._books = {}  # {도서코드: Book}
        self._loans = {}  # {도서코드: Loan}
        for book in books:
            # 코드가 겹치면 뒤의 도서가 앞의 도서를 조용히 덮어써 버린다.
            # 이것은 사용자가 아니라 도서 목록을 만든 프로그래머의 실수이므로
            # LibraryError가 아니라 ValueError로 알린다(실습 6-3 요구 사항 3).
            # __init__에서 예외가 나면 초기화에 실패한 객체는 호출한 쪽에
            # 돌려지지 않으므로, 도서가 겹친 Library는 손에 넣을 수 없다(6.2.1).
            if book.code in self._books:
                raise ValueError(f"도서 코드가 겹칩니다: {book.code}")
            self._books[book.code] = book

    @property
    def loan_count(self) -> int:
        """대출 중인 도서 수."""
        return len(self._loans)

    def find(self, code: str) -> Book:
        """도서 코드(대소문자 구분 없음)로 도서를 찾아 돌려준다.

        없으면 BookNotFoundError를 일으킨다.
        """
        # 딕셔너리에 키가 있는지는 in으로 간단하고 정확하게 검사할 수 있으므로
        # 미리 검사하는 방법을 썼다(6.1.10). try/except KeyError로 쓴다면
        # raise BookNotFoundError(code) from None처럼 쓴다(6.2.5).
        code = code.upper()
        if code not in self._books:
            raise BookNotFoundError(code)
        return self._books[code]

    def late_fee(self, days_over: int) -> int:
        """연체일수 days_over에 따른 연체료(원)를 돌려준다."""
        return days_over * self.LATE_FEE_PER_DAY

    def borrow(self, code: str, who: str, today: date, days: int | None = None) -> Loan:
        """도서를 대출하고, 새로 만든 대출 기록을 돌려준다.

        반납 기한은 today로부터 days일 뒤다. days가 None이면 LOAN_DAYS일이다.
        days가 1보다 작으면 ValueError를 일으킨다.
        없는 도서이면 BookNotFoundError, 대출할 수 없는 도서이면 NotBorrowableError,
        이미 대출 중인 도서이면 AlreadyBorrowedError를 일으킨다.
        """
        # 프로그래머의 실수(잘못된 days)를 먼저 검사한다. 도서 코드와 관계없이
        # 잘못 호출한 코드가 바로 드러나게 하려는 것이다(실습 6-3 "확인할 것" 2번).
        if days is None:
            days = self.LOAN_DAYS
        if days < 1:
            raise ValueError(f"대출 기간은 1일 이상이어야 합니다: {days}")

        # find()가 일으킨 BookNotFoundError는 잡지 않는다. 이 메서드는
        # 없는 도서에 대해 할 수 있는 일이 없으므로 호출한 쪽에 맡긴다(실습 6-3 요구 사항 4).
        book = self.find(code)

        # 5장의 "실패하면 메시지를 return"이 "실패하면 raise"로 바뀌었다.
        # 예외는 그 전에 바꾼 것을 되돌려 주지 않는다. 그래서 검사를 모두 끝낸
        # 뒤에 대출 기록을 바꾼다. 예외가 나면 도서관의 상태는 조금도 바뀌지
        # 않는다(6.2.1).
        if not book.can_borrow():
            raise NotBorrowableError(book)
        if book.code in self._loans:
            raise AlreadyBorrowedError(self._loans[book.code])

        loan = Loan(book, who, today + timedelta(days=days))
        self._loans[book.code] = loan
        # 메시지 대신 Loan 객체를 돌려준다. 무엇을 어떻게 보여 줄지는 호출한 쪽이 정한다.
        return loan

    def return_book(self, code: str, today: date) -> Loan:
        """도서를 반납하고, 끝난 대출 기록을 돌려준다.

        없는 도서이면 BookNotFoundError, 대출 중인 도서가 아니면 NotBorrowedError를 일으킨다.
        """
        # find()로 도서부터 찾으므로, 없는 도서 코드이면 5장과 달리
        # "없는 도서 코드입니다"가 안내된다.
        book = self.find(code)
        if book.code not in self._loans:
            raise NotBorrowedError(book)
        # pop()은 기록을 지우면서 지운 값(Loan)을 돌려준다(3.4).
        # 연체료 계산은 돌려받은 Loan으로 main()이 한다. 그래서 이 버전에서는
        # today를 쓰지 않는다(ch06.md의 주어진 코드 아래 설명 참고).
        return self._loans.pop(book.code)

    # ---- 7장에서 더한 메서드 ----
    # Library는 파일을 모른다(실습 7-4 요구 사항 2). 대출 기록을 딕셔너리의 리스트로
    # 내보내고 받아들일 뿐, 그것을 어디에 어떻게 저장할지는 바깥의 함수가 정한다.

    def loans(self) -> list[Loan]:
        """대출 기록을 반납 기한 순(기한이 같으면 도서 코드 순)으로 돌려준다."""
        # main()과 write_report()가 _loans에 직접 손대지 않도록 이 메서드를 둔다.
        # 새 리스트를 돌려주므로 받은 쪽에서 리스트를 바꿔도 _loans는 그대로다.
        return sorted(self._loans.values(), key=lambda loan: (loan.due, loan.book.code))

    def export_loans(self) -> list[dict]:
        """대출 기록을 JSON으로 저장할 수 있는 딕셔너리의 리스트로 돌려준다.

        [{"code": "B01", "who": "철수", "due": "2026-11-14"}, ...] 모양이고, 도서 코드 순이다.
        """
        # 7.3.7의 todo_to_dict()와 같은 역할이다. date는 JSON으로 바꿀 수 없으므로
        # isoformat()으로 '2026-11-14' 모양의 문자열로 바꾼다(7.3.6).
        records = []
        for code in sorted(self._loans):
            loan = self._loans[code]
            records.append(
                {"code": loan.book.code, "who": loan.who, "due": loan.due.isoformat()}
            )
        return records

    def import_loans(self, records: list[dict]) -> None:
        """export_loans()가 만든 모양의 리스트로 대출 기록을 바꾼다.

        기록 하나라도 형식이 맞지 않으면 예외를 일으키고, 대출 기록은 하나도 바꾸지 않는다.
        - 리스트가 아니거나, 기록이 딕셔너리가 아니거나, code가 문자열이 아니면 TypeError
        - 키(code, who, due)가 빠졌으면 KeyError
        - who가 빈 문자열이거나 due가 'YYYY-MM-DD' 모양의 문자열이 아니면 ValueError
        - 없는 도서, 대출할 수 없는 도서, 같은 도서가 두 번 나오면 LibraryError의 자식 예외
        """
        # 파일에서 읽은 데이터는 바깥 데이터이므로 입구에서 검사한다(7.3.7).
        # json.load()는 리스트가 아니라 딕셔너리나 숫자를 돌려줄 수도 있다.
        if not isinstance(records, list):
            raise TypeError(f"대출 기록은 리스트여야 합니다: {type(records).__name__}")
        # 6.2.1의 "바꾸기 전에 검사": self._loans가 아니라 새 딕셔너리에 모두
        # 만들어 넣고, 검사가 다 끝난 뒤 마지막 줄에서 한 번에 바꾼다.
        # 중간에 예외가 나면 self._loans는 손대지 않은 상태로 남는다.
        loans = {}
        for record in records:
            if not isinstance(record, dict):
                raise TypeError(f"대출 기록 하나는 딕셔너리여야 합니다: {record!r}")
            # 키가 없으면 KeyError, 없는 도서이면 find()의 BookNotFoundError가
            # 그대로 올라간다. 어느 쪽이든 DataFileError로 바꾸는 일은
            # 파일을 아는 load_loans()가 한다.
            code = record["code"]
            # JSON에서는 "code": null이나 "code": 1도 올바른 문법이다. 검사하지 않으면
            # find() 안의 code.upper()에서 AttributeError가 나는데, load_loans()는
            # 그 예외를 잡지 않으므로 트레이스백으로 끝난다. 문자열인지 먼저 확인한다.
            if not isinstance(code, str):
                raise TypeError(f"도서 코드는 문자열이어야 합니다: {code!r}")
            book = self.find(code)
            who = record["who"]
            if not isinstance(who, str) or not who.strip():
                raise ValueError(f"대출자 이름이 비어 있습니다: {record!r}")
            # date.fromisoformat()은 날짜가 아니면 ValueError, 문자열이 아니면
            # TypeError를 일으킨다. 그런데 파이썬 3.11부터는 '20261114'나
            # '2026-W46-2' 같은 다른 ISO 8601 모양도 받아들인다. 'YYYY-MM-DD'만
            # 허용하려면, 읽은 날짜를 다시 isoformat()으로 바꾼 결과가 원문과
            # 같은지 비교한다. 어느 경우든 "반납 기한이 잘못되었다"는 같은 문제다.
            due_text = record["due"]
            try:
                due = date.fromisoformat(due_text)
            except (TypeError, ValueError):
                due = None
            if due is None or due.isoformat() != due_text:
                raise ValueError(
                    f"반납 기한이 'YYYY-MM-DD' 모양이 아닙니다: {due_text!r}"
                )
            if not book.can_borrow():
                raise NotBorrowableError(book)
            # "이미 대출 중"은 self._loans가 아니라 지금 만드는 loans에서 검사한다.
            # 같은 도서가 파일에 두 번 나온 경우를 잡는 것이다.
            if book.code in loans:
                raise AlreadyBorrowedError(loans[book.code])
            loans[book.code] = Loan(book, who, due)
        self._loans = loans

    def loan_lines(self, today: date, only_overdue: bool = False) -> list[str]:
        """대출 목록을 한 줄에 한 권씩, 문자열의 리스트로 돌려준다.

        기본은 반납 기한이 빠른 순서다(기한이 같으면 도서 코드 순).
        only_overdue가 True이면 연체된 도서만, 연체일수가 긴 순서로 돌려준다.
        """
        # 실습 6-3 요구 사항 2는 find(), borrow(), return_book()이 성공·실패를 메시지로
        # 알리지 말라는 것이다. 목록을 문자열로 만들어 돌려주는 이 메서드와
        # book_lines()는 5장 그대로 두며, 출력은 하지 않고 main()에 맡긴다.
        loans = self.loans()

        if only_overdue:
            loans = filter(lambda loan: loan.overdue_days(today) > 0, loans)
            loans = sorted(loans, key=lambda loan: -loan.overdue_days(today))

        lines = []
        for loan in loans:
            lines.append(loan.line(today))
        return lines

    def book_lines(self) -> list[str]:
        """소장 도서 전체를 도서 코드 순으로 한 줄씩 돌려준다.

        줄 끝에 '대출 가능', '대출 중', '관내 열람' 중 하나를 붙인다.
        """
        lines = []
        for code in sorted(self._books):
            book = self._books[code]
            if not book.can_borrow():
                status = "관내 열람"
            elif code in self._loans:
                status = "대출 중"
            else:
                status = "대출 가능"
            lines.append(f"{code} {book.title} | {status}")
        return lines

    def borrower_lines(self) -> list[str]:
        """대출자별로 대출 중인 도서를 한 줄씩 돌려준다.

        '철수 2권: B01 파이썬 첫걸음, B05 인공지능 개론' 모양이다.
        권수가 많은 사람부터, 권수가 같으면 이름 순이다.
        한 사람의 도서는 반납 기한 순(기한이 같으면 도서 코드 순)이다.
        """
        # 3.4.5의 "그룹으로 모으기" 패턴을 defaultdict로 쓴 것이다(8.2.4).
        # 처음 나온 대출자도 groups[who]가 빈 리스트를 만들어 주므로
        # "키가 없으면 빈 리스트를 먼저 넣는" 두 줄이 필요 없다.
        groups = defaultdict(list)  # {대출자: [Loan, ...]}
        # loans()는 반납 기한 순이므로, 한 사람의 목록도 저절로 기한 순이 된다.
        for loan in self.loans():
            groups[loan.who].append(loan)

        # 권수가 많은 순, 같으면 이름 순. 튜플을 key로 쓰면 앞의 값부터 비교한다(4.5.5).
        # groups는 여기서 읽기만 하고 없는 키를 꺼내지 않는다. defaultdict는
        # 꺼내기만 해도 키가 생기므로(8.2.4), 다 모은 뒤에는 있는 키만 쓴다.
        names = sorted(groups, key=lambda who: (-len(groups[who]), who))
        lines = []
        for who in names:
            books = []
            for loan in groups[who]:
                books.append(f"{loan.book.code} {loan.book.title}")
            lines.append(f"{who} {len(groups[who])}권: {', '.join(books)}")
        return lines

    def __repr__(self):
        return f"Library(도서 {len(self._books)}권, 대출 {self.loan_count}권)"
