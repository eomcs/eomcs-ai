"""6장 실습 6-3 해답 — 도서 대출 관리 프로그램(예외 버전).

ch06.md의 "실습 6-3. 종합"에 주어진 클래스와 메서드의 이름, 매개변수,
독스트링을 그대로 두고 본문을 채운 것이다. 6장까지 배운 문법만 사용한다.
5장 해답(ch05/library.py)과 같은 부분은 그대로 옮겨 왔다.
"""

from dataclasses import dataclass
from datetime import date, timedelta

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

HELP_TEXT = """명령 목록
  대출 도서코드 이름   도서를 대출한다
  반납 도서코드        도서를 반납한다
  목록                 대출 중인 도서를 반납 기한 순으로 보여 준다
  연체                 연체된 도서를 연체일수가 긴 순으로 보여 준다
  도서                 소장 도서와 대출 가능 여부를 보여 준다
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

    def loan_lines(self, today: date, only_overdue: bool = False) -> list[str]:
        """대출 목록을 한 줄에 한 권씩, 문자열의 리스트로 돌려준다.

        기본은 반납 기한이 빠른 순서다(기한이 같으면 도서 코드 순).
        only_overdue가 True이면 연체된 도서만, 연체일수가 긴 순서로 돌려준다.
        """
        # 요구 사항 2는 find(), borrow(), return_book()이 성공·실패를 메시지로
        # 알리지 말라는 것이다. 목록을 문자열로 만들어 돌려주는 이 메서드와
        # book_lines()는 5장 그대로 두며, 출력은 하지 않고 main()에 맡긴다.
        loans = sorted(
            self._loans.values(), key=lambda loan: (loan.due, loan.book.code)
        )

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
    """명령을 반복해서 입력받아 처리한다."""
    library = Library(
        [
            Book("B01", "파이썬 첫걸음"),
            Book("B02", "데이터 과학 입문"),
            Book("B03", "알고리즘 이야기"),
            Book("B04", "웹 개발 기초"),
            Book("B05", "인공지능 개론"),
            ReferenceBook("R01", "파이썬 사전"),
        ]
    )
    today = date.today()

    print("도서 대출 관리 (명령 목록: 도움)")
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
            # try 블록에는 예외가 날 것으로 예상하는 호출만 넣는다.
            # 성공 메시지는 else에서 만든다(6.1.7).
            try:
                loan = library.borrow(code, who, today)
            except LibraryError as e:
                # 도서관 규칙에 맞지 않는 요청만 잡아 메시지로 보여 준다.
                # 버그로 생긴 예외(TypeError 등)는 잡지 않으므로 트레이스백으로
                # 드러난다(요구 사항 5, 6.2.6).
                print(e)
            else:
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

        elif command == "날짜":
            if len(args) != 1:
                print("형식: 날짜 N")
                continue
            # 5장의 isdecimal() 미리 검사 대신 int()로 바꿔 보고 예외를 처리한다.
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
#    잠시 today = date(2026, 10, 31)로 바꿔 실행한다.
#    "날짜 +3"은 int("+3")이 3이므로 받아들여져 오늘이 3일 뒤로 옮겨 간다.
#    5장의 isdecimal() 검사였다면 "+3".isdecimal()이 False라서 거부되었다.
#    int()의 규칙을 그대로 쓰게 된 결과다(6.1.10의 비교표).
#
# 2. 셸에서 시험한 결과의 마지막 줄은 다음과 같다.
#    lib.borrow("B01", "영희", ...)
#      → AlreadyBorrowedError: 이미 대출 중입니다: '파이썬 첫걸음' (철수, 반납 기한 2026-11-14(토))
#    lib.find("x99")
#      → BookNotFoundError: 없는 도서 코드입니다: X99
#    lib.borrow("B02", "철수", date(2026, 10, 31), days=0)
#      → ValueError: 대출 기간은 1일 이상이어야 합니다: 0
#    이 해답은 days를 먼저 검사하므로 B02가 없는 도서인데도 ValueError가 난다.
#    find()를 먼저 하면 BookNotFoundError가 난다. 어느 쪽도 틀리지는 않지만,
#    days=0은 borrow()를 잘못 호출한 코드의 실수이므로 도서 코드와 관계없이
#    항상 드러나는 편이 좋다. find()를 먼저 하면 "있는 도서"로 시험할 때까지
#    이 실수가 BookNotFoundError 뒤에 숨어 있게 된다.
#
# 3. 도서 목록에 Book("B01", "중복 도서")를 추가하면 Library(...)를 만드는 순간
#    ValueError: 도서 코드가 겹칩니다: B01 트레이스백과 함께 프로그램이 멈춘다.
#    이 예외는 main()에서 잡지 않는 것이 맞다. 사용자가 다른 명령을 입력한다고
#    해결되는 문제가 아니라, 도서 목록을 만든 코드를 고쳐야 하는 문제이기
#    때문이다(6.2.6의 3번 원칙 "버그로 생긴 예외는 잡지 말고 고친다").
#    LibraryError로 만들었다면 main()이 잡아서 메시지로 바꿀 수 있는 실패처럼
#    보였을 것이다. 사용자가 일으킬 수 있는 실패와 프로그래머의 실수를
#    예외 클래스로 구분해 둔 것이다.
#
# 4. Loan(book, who)로 바꾸고 "대출 B02 철수"를 입력하면
#    TypeError: Loan.__init__() missing 1 required positional argument: 'due'
#    트레이스백이 나오고 프로그램이 멈춘다. 마지막 File 줄이 borrow()의
#    Loan(...) 줄을 가리키므로 고칠 곳을 바로 알 수 있다.
#    except Exception as e:로 바꾸면 같은 입력에 대해
#    "Loan.__init__() missing 1 required positional argument: 'due'"가
#    마치 대출 실패 안내처럼 출력되고 프로그램은 계속 실행된다. 대출은 되지
#    않았는데 트레이스백도 없어서 원인을 찾기 어렵고, 사용자에게는 알아들을
#    수 없는 메시지다. 코드의 버그가 사용자의 실패로 둔갑한 것이다
#    (6.1.7의 :,d 예와 같은 문제). 그래서 except Exception:을 금지했다.
#
# 5. 메시지 문구를 바꾸려면 5장 버전은 Library.borrow()와 return_book() 안의
#    문자열을, 6장 버전은 실패 메시지는 예외 클래스의 __init__을, 성공 메시지는
#    main()을 고친다. 6장 버전의 Library는 화면에 무엇을 보여 줄지 전혀 모르고
#    결과 객체와 예외만 주고받는다. 그래서 웹 서비스나 다른 프로그램에서
#    다시 쓸 때, 그 프로그램이 Loan 객체와 예외의 종류·속성(e.loan, e.book)을
#    보고 자기 화면에 맞는 안내를 만들 수 있다. 5장 버전은 한국어 안내 문장을
#    돌려주므로, 다른 화면에서 쓰려면 그 문장을 다시 해석해야 한다.
# ---------------------------------------------------------------------------
