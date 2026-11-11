"""도서관 프로그램의 예외 클래스.

메시지를 만들 때 Book, Loan, format_date()를 쓰므로 models만 가져온다.
"""

from pathlib import Path

from library.models import Book, Loan, format_date

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
