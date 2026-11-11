"""도서 대출 관리 패키지.

자주 쓰는 이름을 여기서 다시 내보낸다. 그래서 바깥에서는
from library import Library, load_books처럼 하위 모듈 이름 없이 가져올 수 있다.
"""

from library.core import Library
from library.errors import (
    AlreadyBorrowedError,
    BookNotFoundError,
    DataFileError,
    LibraryError,
    NotBorrowableError,
    NotBorrowedError,
)
from library.models import Book, Loan, ReferenceBook
from library.storage import load_books, load_loans, save_loans, write_report

# from library import *로 가져갈 이름이자, "이 이름들은 일부러 다시 내보낸다"는 표시다.
__all__ = [
    "AlreadyBorrowedError",
    "Book",
    "BookNotFoundError",
    "DataFileError",
    "Library",
    "LibraryError",
    "Loan",
    "NotBorrowableError",
    "NotBorrowedError",
    "ReferenceBook",
    "load_books",
    "load_loans",
    "save_loans",
    "write_report",
]
