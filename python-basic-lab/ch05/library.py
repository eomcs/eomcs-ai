"""5장 실습 5-5 해답 — 도서 대출 관리 프로그램(클래스 버전).

ch05.md의 "실습 5-5. 종합"에 주어진 클래스와 메서드의 이름, 매개변수,
독스트링을 그대로 두고 본문을 채운 것이다. 5장까지 배운 문법만 사용한다.
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
    # 어떤 객체에도 속하지 않는 짧은 계산이므로 함수로 둔다.
    return f"{d.strftime('%Y-%m-%d')}({WEEKDAYS[d.weekday()]})"


# find()가 도서관이 가진 Book 객체를 그대로 돌려주므로, 바깥에서 code나
# title을 바꾸지 못하도록 frozen=True로 둔다(5.4.6, 실습 5-5 요구 사항 6).
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

    # 새 필드가 없으므로 @dataclass를 다시 붙이지 않는다.
    # __init__, __repr__, __eq__, __str__과 필드를 바꿀 수 없는 성질을
    # Book에게서 물려받는다.

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


class Library:
    """도서관. 소장 도서와 대출 기록을 관리한다."""

    LOAN_DAYS = 14
    LATE_FEE_PER_DAY = 100

    def __init__(self, books: list[Book]):
        """books의 도서를 소장한다. 대출 기록은 비어 있는 상태로 시작한다."""
        self._books = {}  # {도서코드: Book}
        self._loans = {}  # {도서코드: Loan}
        # 받은 리스트를 그대로 저장하지 않고, 코드로 빨리 찾을 수 있게
        # 딕셔너리를 새로 만든다. 그래서 바깥의 리스트가 바뀌어도 영향이 없다.
        for book in books:
            self._books[book.code] = book

    @property
    def loan_count(self) -> int:
        """대출 중인 도서 수."""
        return len(self._loans)

    def find(self, code: str) -> Book | None:
        """도서 코드(대소문자 구분 없음)로 도서를 찾아 돌려준다. 없으면 None."""
        return self._books.get(code.upper())

    def late_fee(self, days_over: int) -> int:
        """연체일수 days_over에 따른 연체료(원)를 돌려준다."""
        # Library.LATE_FEE_PER_DAY가 아니라 self.LATE_FEE_PER_DAY로 읽으므로
        # 자식 클래스가 클래스 속성을 오버라이딩하면 그 값이 쓰인다.
        return days_over * self.LATE_FEE_PER_DAY

    def borrow(self, code: str, who: str, today: date, days: int | None = None) -> str:
        """도서를 대출하고, 화면에 출력할 결과 메시지를 돌려준다.

        반납 기한은 today로부터 days일 뒤다. days가 None이면 LOAN_DAYS일이다.
        없는 도서, 대출할 수 없는 도서, 이미 대출 중인 도서이면 대출하지 않는다.
        """
        # 실패하는 경우를 먼저 처리하고 바로 돌려준다(조기 반환, 4.1.5).
        book = self.find(code)
        if book is None:
            return f"없는 도서 코드입니다: {code.upper()}"
        # 종류를 isinstance()로 묻지 않고 도서에게 맡긴다(다형성, 5.3.5).
        if not book.can_borrow():
            return f"대출할 수 없는 참고 도서입니다: {book}"
        if book.code in self._loans:
            loan = self._loans[book.code]
            return f"이미 대출 중입니다: {book} ({loan.who}, 반납 기한 {format_date(loan.due)})"

        # 기본값을 days=LOAN_DAYS로 두면 def 문이 실행될 때 한 번 정해지므로(4.2.4)
        # 자식 클래스에서 LOAN_DAYS를 바꿔도 반영되지 않는다. 그래서 None을 쓴다.
        if days is None:
            days = self.LOAN_DAYS
        due = today + timedelta(days=days)
        self._loans[book.code] = Loan(book, who, due)
        return f"{book} 대출 완료 - {who}, 반납 기한 {format_date(due)}"

    def return_book(self, code: str, today: date) -> str:
        """도서를 반납하고, 화면에 출력할 결과 메시지를 돌려준다.

        연체되었으면 메시지에 연체일수와 연체료를 포함한다.
        """
        code = code.upper()
        if code not in self._loans:
            return f"대출 중인 도서가 아닙니다: {code}"

        loan = self._loans.pop(code)
        days_over = loan.overdue_days(today)
        if days_over == 0:
            return f"{loan.book} 반납 완료"
        return f"{loan.book} 반납 완료 - {days_over}일 연체, 연체료 {self.late_fee(days_over):,}원"

    def loan_lines(self, today: date, only_overdue: bool = False) -> list[str]:
        """대출 목록을 한 줄에 한 권씩, 문자열의 리스트로 돌려준다.

        기본은 반납 기한이 빠른 순서다(기한이 같으면 도서 코드 순).
        only_overdue가 True이면 연체된 도서만, 연체일수가 긴 순서로 돌려준다.
        """
        # 4장의 item[1]["due"], item[0]이 loan.due, loan.book.code가 되었다.
        # sorted()는 새 리스트를 돌려주므로 self._loans는 그대로다.
        loans = sorted(
            self._loans.values(), key=lambda loan: (loan.due, loan.book.code)
        )

        if only_overdue:
            loans = filter(lambda loan: loan.overdue_days(today) > 0, loans)
            # 안정 정렬이므로 연체일수가 같으면 위의 순서(기한 → 코드)가 유지된다.
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
            # 대소문자 처리는 Library가 하므로 code.upper()를 하지 않는다.
            code, who = args
            print(library.borrow(code, who, today))

        elif command == "반납":
            if len(args) != 1:
                print("형식: 반납 도서코드")
                continue
            print(library.return_book(args[0], today))

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
            # and는 왼쪽이 거짓이면 오른쪽을 계산하지 않으므로
            # 숫자가 아닌 문자열이 int()에 들어가는 일은 없다(실습 3-7).
            if not (args[0].isdecimal() and int(args[0]) >= 1):
                print("날짜는 1 이상의 정수로 입력하세요.")
                continue
            # today는 main()의 지역 변수이므로 global이 필요 없다.
            today = today + timedelta(days=int(args[0]))
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
#
# 2. lib.loan_count = 0은 AttributeError: property 'loan_count' of 'Library'
#    object has no setter 오류가 난다. loan_count는 setter가 없는 프로퍼티이므로
#    바깥 코드는 대출 수를 읽을 수만 있다. 대출 수는 borrow()와 return_book()이
#    _loans를 바꿀 때만 달라지므로, 대출 기록과 대출 수가 어긋날 수 없다.
#    lib.find("r01")은 ReferenceBook(code='R01', title='파이썬 사전')을 보여 준다.
#    Book에서 물려받은 __repr__이 type(self)의 이름을 쓰기 때문이다.
#
#    lib.find("b01").code = "B99"는 dataclasses.FrozenInstanceError:
#    cannot assign to field 'code' 오류가 난다. frozen=True를 빼면 할당은
#    되지만, _books의 키는 "B01"인데 Book 객체의 code는 "B99"가 된다.
#    borrow("B01", ...)은 find()가 _books의 키 "B01"로 찾으므로 성공하지만
#    대출 기록은 book.code인 "B99"를 키로 _loans에 들어간다. 그래서
#    return_book("B01", ...)은 _loans에서 "B01"을 찾지 못해 실패한다.
#    바깥에 내준 객체를 바꿀 수 있으면 도서관 내부가 어긋난다.
#
# 3. 4장의 borrow(loans, code.upper(), who, today)가
#    library.borrow(code, who, today)가 되었다. 인자에서 loans가 사라졌고,
#    대소문자 처리도 main()에서 Library로 옮겨 갔다. main()은 대출 기록이
#    딕셔너리라는 사실도, 대출 한 건이 Loan 객체라는 사실도 알 필요가 없다.
#    Library 안의 저장 방식을 바꿔도 main()은 고칠 필요가 없다.
#
# 4. borrow() 안에서 self._loans[book.code] = Loan(book, who, due) 줄을
#    지나는 순간 변수 패널의 self → _loans에 항목이 하나 생기고,
#    그 Loan 객체를 펼치면 book 필드에 Book 객체가 들어 있다.
# ---------------------------------------------------------------------------
