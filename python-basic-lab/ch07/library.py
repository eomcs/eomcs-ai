"""7장 실습 7-4 해답 — 도서 대출 관리 프로그램(파일 저장 버전).

ch07.md의 "실습 7-4. 종합"에 주어진 클래스와 함수의 이름, 매개변수,
독스트링을 그대로 두고 본문을 채운 것이다. 7장까지 배운 문법만 사용한다.
6장 해답(ch06/library.py)과 같은 부분은 그대로 옮겨 왔다.

실행하려면 이 파일 옆에 data/books.csv가 있어야 한다(ch07.md 참고).
data/loans.json은 처음 실행할 때는 없어도 되고, 프로그램이 만든다.
"""

import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

# 데이터 파일은 프로그램과 한 묶음이므로 현재 디렉터리가 아니라 이 스크립트가
# 있는 폴더를 기준으로 정한다(7.2.4). 그래서 어느 폴더에서 실행하든,
# VS Code의 ▷ 버튼으로 실행하든 같은 파일을 읽고 쓴다(요구 사항 3).
DATA_DIR = Path(__file__).parent / "data"
BOOKS_PATH = DATA_DIR / "books.csv"
LOANS_PATH = DATA_DIR / "loans.json"
REPORT_PATH = DATA_DIR / "loan_report.csv"

HELP_TEXT = """명령 목록
  대출 도서코드 이름   도서를 대출한다
  반납 도서코드        도서를 반납한다
  목록                 대출 중인 도서를 반납 기한 순으로 보여 준다
  연체                 연체된 도서를 연체일수가 긴 순으로 보여 준다
  도서                 소장 도서와 대출 가능 여부를 보여 준다
  보고서               대출 목록을 엑셀에서 열 수 있는 CSV 파일로 저장한다
  날짜 N               오늘 날짜를 N일 뒤로 옮긴다 (시험용)
  도움                 이 목록을 보여 준다
  종료                 프로그램을 끝낸다"""


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


# 예외 클래스는 Book과 Loan 아래에 둔다. 타입 힌트에서 두 클래스를 쓰기 때문이다.
# 프로그램을 쓰는 사람의 요청이 도서관 규칙에 맞지 않을 때 일으키는 예외는
# 모두 LibraryError의 자식으로 만든다. main()은 LibraryError 하나만 잡으면
# 지금 있는 실패와 앞으로 추가될 실패를 모두 처리할 수 있다(6.2.4).


class LibraryError(Exception):
    """도서관의 규칙에 맞지 않는 요청일 때 일으키는 예외의 부모 클래스."""


class BookNotFoundError(LibraryError):
    """도서 코드에 해당하는 도서가 없다."""

    def __init__(self, code: str):
        super().__init__(f"없는 도서 코드입니다: {code}")
        self.code = code


class NotBorrowableError(LibraryError):
    """대출할 수 없는 도서(참고 도서)를 대출하려 했다."""

    def __init__(self, book: Book):
        """메시지는 "대출할 수 없는 참고 도서입니다: '파이썬 사전'"이다. 속성 book에 그 도서를 담는다."""
        # {book}은 Book.__str__이 만든 '제목' 모양이 된다.
        # super().__init__()에 메시지를 넘겨야 str(e)가 이 메시지를 돌려준다.
        super().__init__(f"대출할 수 없는 참고 도서입니다: {book}")
        self.book = book


class AlreadyBorrowedError(LibraryError):
    """이미 대출 중인 도서를 대출하려 했다."""

    def __init__(self, loan: Loan):
        """메시지는 "이미 대출 중입니다: '파이썬 첫걸음' (철수, 반납 기한 2026-11-14(토))"이다.

        속성 loan에 지금 대출 중인 기록을 담는다.
        """
        super().__init__(
            f"이미 대출 중입니다: {loan.book} ({loan.who}, 반납 기한 {format_date(loan.due)})"
        )
        self.loan = loan


class NotBorrowedError(LibraryError):
    """대출 중이 아닌 도서를 반납하려 했다."""

    def __init__(self, book: Book):
        """메시지는 "대출 중인 도서가 아닙니다: B02"이다. 속성 book에 그 도서를 담는다."""
        super().__init__(f"대출 중인 도서가 아닙니다: {book.code}")
        self.book = book


# 데이터 파일의 문제는 LibraryError(사용자의 요청이 규칙에 맞지 않음)도
# 아니고 프로그래머의 실수(ValueError)도 아니다. 파일을 고칠 사람에게
# 알려야 하는 별개의 실패이므로 따로 둔다.
class DataFileError(Exception):
    """데이터 파일의 내용이 형식에 맞지 않는다."""

    def __init__(self, path: Path, reason: str):
        super().__init__(f"데이터 파일 오류 ({path.name}): {reason}")
        self.path = path
        self.reason = reason


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
            # LibraryError가 아니라 ValueError로 알린다(요구 사항 3).
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
        # 잘못 호출한 코드가 바로 드러나게 하려는 것이다("확인할 것" 2번).
        if days is None:
            days = self.LOAN_DAYS
        if days < 1:
            raise ValueError(f"대출 기간은 1일 이상이어야 합니다: {days}")

        # find()가 일으킨 BookNotFoundError는 잡지 않는다. 이 메서드는
        # 없는 도서에 대해 할 수 있는 일이 없으므로 호출한 쪽에 맡긴다(요구 사항 4).
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
    # Library는 파일을 모른다(요구 사항 2). 대출 기록을 딕셔너리의 리스트로
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
        # 요구 사항 2는 find(), borrow(), return_book()이 성공·실패를 메시지로
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

    def __repr__(self):
        return f"Library(도서 {len(self._books)}권, 대출 {self.loan_count}권)"


def load_books(path: Path) -> list[Book]:
    """CSV 파일에서 도서 목록을 읽어 돌려준다.

    첫 줄은 code,title,kind여야 한다. kind가 '일반'이면 Book, '참고'이면 ReferenceBook을 만든다.
    도서 코드는 앞뒤 공백을 지우고 대문자로 바꾼다.
    파일이 없으면 FileNotFoundError를 그대로 보낸다.
    UTF-8로 읽을 수 없거나 내용이 형식에 맞지 않으면 DataFileError를 일으킨다.
    형식 오류의 메시지에는 파일의 몇 번째 줄인지 넣는다.
    """
    # 엑셀에서 'CSV UTF-8'로 저장한 파일은 맨 앞에 BOM이 붙는다. utf-8로 읽으면
    # 첫 열 이름이 '\ufeffcode'가 되어 헤더 검사에 걸리므로 utf-8-sig로 연다.
    # BOM이 없는 파일도 utf-8-sig로 문제없이 읽힌다(7.3.3).
    # 파일이 없을 때의 FileNotFoundError는 잡지 않는다. 이 함수는 도서 목록
    # 파일이 없을 때 할 수 있는 일이 없으므로 main()에 맡긴다(요구 사항 4).
    #
    # 첫 번째 단계: 파일을 읽기만 한다. 엑셀의 'CSV' 형식이나 오래된 메모장으로
    # 저장한 파일은 CP949라서 읽는 도중에 UnicodeDecodeError가 난다(7.1.7).
    # 이 예외만 DataFileError로 바꾸려고, try 블록에는 읽는 코드만 둔다.
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = []
            for row in reader:
                # DictReader는 빈 줄을 건너뛰고, 따옴표 안에 줄바꿈이 있는 값은
                # 여러 줄을 한 레코드로 읽는다. 그래서 레코드 수를 세면 파일의
                # 줄 번호와 어긋난다. line_num은 지금까지 읽은 파일의 줄 수,
                # 즉 이 레코드의 마지막 줄 번호다. 편집기에서 찾을 줄과 같다.
                rows.append((reader.line_num, row))
    except UnicodeDecodeError as e:
        raise DataFileError(
            path, "UTF-8로 읽을 수 없습니다. 엑셀에서는 'CSV UTF-8' 형식으로 저장하세요"
        ) from e

    # 두 번째 단계: 읽은 내용을 검사하고 도서를 만든다.
    # 빈 파일이면 fieldnames가 None이므로 이 검사에 함께 걸린다.
    if fieldnames != ["code", "title", "kind"]:
        raise DataFileError(path, "첫 줄은 code,title,kind여야 합니다")
    books = []
    codes = set()  # 지금까지 나온 도서 코드. 겹치는지 검사한다
    for line_no, row in rows:
        # 칸이 모자란 줄은 DictReader가 None으로 채운다. None or ""는 ""이므로
        # None과 빈 문자열을 한꺼번에 처리할 수 있다.
        code = (row["code"] or "").strip().upper()
        title = (row["title"] or "").strip()
        kind = (row["kind"] or "").strip()
        if not code or not title:
            raise DataFileError(
                path, f"{line_no}번째 줄: 도서 코드와 제목이 있어야 합니다"
            )
        # 6장에서는 같은 검사를 Library.__init__이 ValueError로 했다(그 검사는
        # 안전망으로 그대로 남아 있다). 이제 도서 목록은 파일에서 오고,
        # 고칠 사람은 프로그래머가 아니라 파일을 편집한 사람이다. 그래서
        # 줄 번호와 함께 DataFileError로 먼저 알려 준다.
        if code in codes:
            raise DataFileError(path, f"{line_no}번째 줄: 도서 코드가 겹칩니다: {code}")
        if kind == "일반":
            books.append(Book(code, title))
        elif kind == "참고":
            books.append(ReferenceBook(code, title))
        else:
            raise DataFileError(
                path,
                f"{line_no}번째 줄: kind는 '일반'이나 '참고'여야 합니다: {kind!r}",
            )
        codes.add(code)
    return books


def load_loans(library: Library, path: Path) -> None:
    """JSON 파일에서 대출 기록을 읽어 library에 채운다.

    파일이 없으면 처음 실행한 것이므로 아무것도 하지 않는다.
    UTF-8로 읽을 수 없거나, JSON 형식이 잘못되었거나, 내용이 맞지 않으면
    DataFileError를 일으킨다.
    """
    # 첫 번째 단계: 파일을 읽어 JSON을 파이썬 데이터로 바꾼다.
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        # 프로그램이 스스로 관리하는 저장 파일이 처음에 없는 것은 정상이다(7.1.8).
        return
    except UnicodeDecodeError as e:
        # CP949 등으로 저장된 파일. JSON 표준은 UTF-8이다(7.3.6).
        raise DataFileError(path, "UTF-8로 읽을 수 없습니다") from e
    except json.JSONDecodeError as e:
        raise DataFileError(path, f"JSON 형식이 아닙니다 ({e})") from e

    # 두 번째 단계: 데이터를 Library에 넣는다. try 블록에는 import_loans() 호출
    # 한 줄만 둔다. 넓게 감싸면 내 코드의 버그로 생긴 예외까지 "데이터 파일 오류"로
    # 둔갑한다(6.1.7). 원래 예외는 from e로 연결해 디버깅할 때 볼 수 있게 한다(6.2.5).
    try:
        library.import_loans(records)
    except KeyError as e:
        # KeyError의 메시지는 "'who'"처럼 키 이름뿐이라서 따로 바꿔 준다.
        raise DataFileError(path, f"대출 기록에 {e} 항목이 없습니다") from e
    except (TypeError, ValueError, LibraryError) as e:
        raise DataFileError(path, str(e)) from e


def save_loans(library: Library, path: Path) -> None:
    """library의 대출 기록을 JSON 파일로 저장한다. 폴더가 없으면 만든다."""
    # open()은 파일은 만들어 주지만 폴더는 만들어 주지 않는다(7.2.3).
    # "w" 모드는 여는 순간 기존 내용을 지운다(7.1.5). 그래서 main()은 loans.json을
    # 제대로 읽지 못했을 때 이 함수가 실행될 일이 없도록 프로그램을 끝낸다.
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(library.export_loans(), f, ensure_ascii=False, indent=2)


def write_report(library: Library, path: Path, today: date) -> int:
    """대출 목록을 엑셀에서 열 수 있는 CSV 파일로 저장하고, 저장한 도서 수를 돌려준다.

    열은 도서코드, 제목, 대출자, 반납기한, 연체일수이고, 반납 기한 순이다.
    """
    # 엑셀에서 한글이 깨지지 않도록 BOM을 붙이는 utf-8-sig로, csv 모듈이 줄바꿈을
    # 직접 처리하도록 newline=""으로 연다(7.3.3). 대출이 없어도 헤더만 있는 파일을 만든다.
    loans = library.loans()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["도서코드", "제목", "대출자", "반납기한", "연체일수"])
        for loan in loans:
            writer.writerow(
                [
                    loan.book.code,
                    loan.book.title,
                    loan.who,
                    loan.due.isoformat(),
                    loan.overdue_days(today),
                ]
            )
    return len(loans)


def print_lines(lines: list[str], empty_message: str) -> None:
    """lines를 한 줄씩 출력한다. 비어 있으면 empty_message를 출력한다."""
    if not lines:
        print(empty_message)
    for line in lines:
        print(line)


def parse_days(text: str) -> int:
    """'날짜 N'의 N을 정수로 바꿔 돌려준다. 1 이상의 정수가 아니면 ValueError를 일으킨다."""
    # 정수인지는 int()에게 맡기고(일단 해 보기), 1 이상인지는 직접 검사한다(6.1.10).
    # int()가 일으킨 ValueError는 잡지 않고 그대로 보낸다. 1보다 작을 때도
    # 같은 ValueError를 일으키므로, main()은 except ValueError 하나로
    # 두 경우를 함께 처리할 수 있다.
    days = int(text)
    if days < 1:
        raise ValueError(f"날짜는 1 이상이어야 합니다: {days}")
    return days


def main():
    """데이터 파일을 읽어 도서관을 준비한 뒤, 명령을 반복해서 입력받아 처리한다."""
    # 같은 "파일이 없다"도 파일의 의미에 따라 다르게 대처한다(7.1.8).
    # 도서 목록은 프로그램이 동작하는 데 꼭 필요하므로 없으면 알리고 끝낸다.
    try:
        books = load_books(BOOKS_PATH)
    except FileNotFoundError:
        print(f"도서 목록 파일이 없습니다: {BOOKS_PATH}")
        return
    except DataFileError as e:
        print(e)
        return

    library = Library(books)
    try:
        load_loans(library, LOANS_PATH)
    except DataFileError as e:
        # 빈 대출 기록으로 시작하면 다음 대출·반납 때 save_loans()가 "w" 모드로
        # loans.json을 덮어써서, 파일에 남아 있던 기록이 모두 사라진다.
        # 그래서 시작하지 않고 사람이 파일을 고치게 한다(요구 사항 6).
        print(e)
        print(
            "파일을 고친 뒤 다시 실행하세요. 기록을 지키기 위해 프로그램을 시작하지 않습니다."
        )
        return

    today = date.today()

    print("도서 대출 관리 (명령 목록: 도움)")
    print(f"도서 {len(books)}권, 대출 기록 {library.loan_count}건을 불러왔습니다.")
    print(f"오늘: {format_date(today)}")

    while True:
        words = input("> ").split()
        if not words:
            continue

        command, *args = words

        if command == "종료":
            print("프로그램을 종료합니다.")
            break

        elif command == "대출":
            if len(args) != 2:
                print("형식: 대출 도서코드 이름")
                continue
            code, who = args
            try:
                loan = library.borrow(code, who, today)
            except LibraryError as e:
                print(e)
            else:
                # 성공했을 때만 저장한다. 바뀔 때마다 곧바로 저장하므로, 저장이
                # 끝난 뒤라면 Ctrl+C로 멈추거나 프로그램이 비정상적으로 끝나도
                # 기록이 남는다(요구 사항 7). 저장하는 도중에 끊기면 "w"로 이미
                # 지운 파일이 비거나 반만 쓰인 채 남을 수 있다("더 해 보기" 참고).
                save_loans(library, LOANS_PATH)
                print(
                    f"{loan.book} 대출 완료 - {loan.who}, 반납 기한 {format_date(loan.due)}"
                )

        elif command == "반납":
            if len(args) != 1:
                print("형식: 반납 도서코드")
                continue
            try:
                loan = library.return_book(args[0], today)
            except LibraryError as e:
                print(e)
            else:
                save_loans(library, LOANS_PATH)
                days_over = loan.overdue_days(today)
                if days_over == 0:
                    print(f"{loan.book} 반납 완료")
                else:
                    fee = library.late_fee(days_over)
                    print(
                        f"{loan.book} 반납 완료 - {days_over}일 연체, 연체료 {fee:,}원"
                    )

        elif command == "목록":
            if len(args) != 0:
                print("형식: 목록")
                continue
            print_lines(library.loan_lines(today), "대출 중인 도서가 없습니다.")

        elif command == "연체":
            if len(args) != 0:
                print("형식: 연체")
                continue
            print_lines(
                library.loan_lines(today, only_overdue=True), "연체된 도서가 없습니다."
            )

        elif command == "도서":
            if len(args) != 0:
                print("형식: 도서")
                continue
            print_lines(library.book_lines(), "소장 도서가 없습니다.")

        elif command == "보고서":
            if len(args) != 0:
                print("형식: 보고서")
                continue
            count = write_report(library, REPORT_PATH, today)
            print(f"대출 {count}건을 저장했습니다: {REPORT_PATH}")

        elif command == "날짜":
            if len(args) != 1:
                print("형식: 날짜 N")
                continue
            try:
                days = parse_days(args[0])
            except ValueError:
                print("날짜는 1 이상의 정수로 입력하세요.")
            else:
                today = today + timedelta(days=days)
                print(f"오늘: {format_date(today)}")

        elif command == "도움":
            print(HELP_TEXT)

        else:
            print("알 수 없는 명령입니다. '도움'을 입력하세요.")


main()


# ---------------------------------------------------------------------------
# "확인할 것" 참고 답
#
# 1. 실행 예와 같은 결과를 확인하려면 main()의 today = date.today()를
#    잠시 today = date(2026, 10, 31)로 바꾸고, data/loans.json을 지운 뒤 실행한다.
#
# 2. DATA_DIR이 Path(__file__).parent를 기준으로 하므로 python-lab 폴더에서
#    python ch07/library.py로 실행해도, VS Code의 ▷ 버튼으로 실행해도
#    같은 ch07/data/loans.json을 읽는다.
#
# 3. 오류 상황별로 예외를 잡는 곳은 다음과 같다.
#    - books.csv의 kind 오류, 코드 겹침 → load_books()가 DataFileError
#    - books.csv 없음 → open()의 FileNotFoundError를 main()이 잡는다
#    - loans.json의 끝 쉼표 → json.load()의 JSONDecodeError를 load_loans()가 바꾼다
#    - 없는 도서 코드 → find()의 BookNotFoundError(LibraryError)를 load_loans()가 바꾼다
#    - who 없음 → KeyError를 load_loans()가 바꾼다
#    - 없는 날짜, '20261114' 같은 다른 모양 → import_loans()가 ValueError로 바꾸고,
#      load_loans()가 다시 바꾼다
#    - "code": null → import_loans()가 TypeError를 일으키고, load_loans()가 바꾼다
#    - CP949로 저장한 파일 → UnicodeDecodeError를 load_books()/load_loans()가 바꾼다
#    - books.csv에 빈 줄이나 여러 줄짜리 값이 있어도 reader.line_num 덕분에
#      메시지의 줄 번호는 편집기에서 보이는 줄 번호와 같다
#
# 4. loans.json이 빈 파일이면
#    "데이터 파일 오류 (loans.json): JSON 형식이 아닙니다 (Expecting value: line 1 column 1 (char 0))"
#    가 나오고 프로그램이 시작하지 않는다. 이 해답은 빈 파일을 오류로 처리했다.
#    save_loans()는 대출 기록이 없어도 []를 쓰므로, 이 프로그램이 정상적으로
#    만든 loans.json은 빈 파일일 수 없다. 빈 파일은 "w"로 열어 내용을 지운 직후
#    json.dump()가 끝나기 전에 컴퓨터가 꺼지는 경우처럼 저장이 실패했을 때
#    생긴다. 그때의 "기록 없음"은 진짜로 기록이 없다는 뜻이 아니므로,
#    조용히 빈 기록으로 시작하는 것보다 알리는 편이 안전하다.
#    ("더 해 보기"의 안전하게 저장하기를 하면 이런 빈 파일이 생기지 않는다.)
#
# 5. 빈 기록으로 시작한 뒤 대출을 한 번 하면 save_loans()가 loans.json을 "w"
#    모드로 연다. "w"는 여는 순간 기존 내용을 지우므로(7.1.5), 파일에 있던
#    기록은 모두 사라지고 방금 한 대출 한 건만 남는다. 파일의 사소한 오타 하나
#    때문에 모든 대출 기록을 잃게 되는 것이다. 그래서 시작하지 않는다.
#
# 6. "대출 완료" 메시지가 나온 뒤에 Ctrl+C로 멈추면, 그 전에 저장이 끝났으므로
#    기록이 남아 있다. 저장하는 도중(open()으로 "w" 모드로 연 뒤 json.dump()가
#    끝나기 전)에 끊기거나 쓰기가 실패하면 기존 내용은 이미 지워졌으므로
#    빈 파일이나 반만 쓰인 파일이 남는다. 즉시 저장은 "저장이 끝난 기록"만
#    지켜 준다. 저장 도중의 사고까지 막으려면 "더 해 보기"의 임시 파일 교체를 쓴다.
#    종료할 때만 저장한다면 Ctrl+C, 정전, 처리하지 않은 예외로 프로그램이
#    끝날 때 그때까지의 기록이 모두 사라진다. 바뀔 때마다 저장하는 방식의
#    단점은 매번 파일 전체를 다시 쓰므로 기록이 아주 많으면 느려진다는 것이다.
#    (그런 경우에는 7.3.8의 JSONL처럼 바뀐 것만 덧붙이거나 데이터베이스를 쓴다.)
#
# 7. 6장에서 도서 목록은 main() 안의 코드였다. 코드가 겹치면 고칠 사람은
#    프로그래머이고, 프로그램이 실행 중에 대처할 방법이 없으므로 잡지 않았다.
#    7장에서는 도서 목록이 파일에서 온다. 고칠 사람은 books.csv를 편집한
#    사서이고, 그 사람에게 "몇 번째 줄이 왜 잘못되었는지" 알려 주는 것이
#    프로그램이 할 수 있는 대처다. 그래서 load_books()가 줄 번호와 함께
#    DataFileError로 알리고 main()이 잡아 메시지를 보여 준다(6.2.6).
#    같은 문제라도 데이터가 어디서 오느냐에 따라 책임과 처리가 달라진다.
#
# 8. 대출 기록을 데이터베이스에 저장하기로 하면 load_loans()와 save_loans()만
#    고치면 된다. Library는 export_loans()/import_loans()로 딕셔너리의 리스트만
#    주고받으므로 고칠 필요가 없다. 파일 없이 시험할 수도 있다.
#    >>> lib = Library(load_books(BOOKS_PATH))
#    >>> lib.import_loans([{"code": "B01", "who": "철수", "due": "2026-11-14"}])
#    >>> lib.loans()
#    [Loan(book=Book(code='B01', title='파이썬 첫걸음'), who='철수', due=datetime.date(2026, 11, 14))]
#    >>> lib.import_loans([{"code": "B01", "who": "철수", "due": "2026-11-14"},
#    ...                   {"code": "X99", "who": "영희", "due": "2026-11-14"}])
#    BookNotFoundError: 없는 도서 코드입니다: X99
#    >>> lib.loan_count
#    1
#    두 번째 import_loans()가 실패해도 대출 기록은 앞의 1건 그대로다.
#    새 딕셔너리에 모두 만든 뒤 마지막에 바꾸기 때문이다.
# ---------------------------------------------------------------------------
