"""명령을 입력받아 처리하는 화면 쪽 코드. 프로그램의 시작점인 main()이 있다.

패키지의 다른 모듈을 모두 가져다 쓴다. models, errors, core, storage는 이 모듈을
가져오지 않는다. 이 모듈을 가져오는 것은 시작 파일(main.py, __main__.py)뿐이다.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

from library.core import Library
from library.errors import DataFileError, LibraryError
from library.models import format_date
from library.storage import load_books, load_loans, save_loans, write_report

# 기본 데이터 폴더는 패키지 폴더(library)의 부모 폴더 안의 data다(ch08/data).
# 이 파일은 library/cli.py이므로 parent는 library, parent.parent는 ch08이다.
# 7장의 library.py는 ch07 바로 아래에 있어서 parent 한 번이면 됐다(8.3.5).
# 7장의 BOOKS_PATH 같은 파일 경로 상수는 두지 않는다. 데이터 폴더는 실행할 때
# 명령행 인자로 정해지므로, 파일 경로는 main() 안에서 만든다.
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"

HELP_TEXT = """명령 목록
  대출 도서코드 이름   도서를 대출한다
  반납 도서코드        도서를 반납한다
  목록                 대출 중인 도서를 반납 기한 순으로 보여 준다
  연체                 연체된 도서를 연체일수가 긴 순으로 보여 준다
  대출자               대출자별로 대출 중인 도서를 보여 준다
  도서                 소장 도서와 대출 가능 여부를 보여 준다
  보고서               대출 목록을 엑셀에서 열 수 있는 CSV 파일로 저장한다
  날짜 N               오늘 날짜를 N일 뒤로 옮긴다 (시험용)
  도움                 이 목록을 보여 준다
  종료                 프로그램을 끝낸다"""


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
    # 데이터 폴더를 명령행 인자로 받을 수 있다(8.2.2). sys.argv[0]은 실행한
    # 스크립트(python -m library로 실행하면 library/__main__.py)이고, 인자는
    # sys.argv[1]부터 들어온다. 사용자가 지정한 경로이므로 Path(__file__)이 아니라
    # 현재 디렉터리를 기준으로 한다(7.2.4). 지정하지 않으면 기본 폴더를 쓴다.
    # 사용법이 잘못되었을 때는 종료 코드 2를 남기는 것이 관례다.
    if len(sys.argv) > 2:
        print("사용법: python main.py [데이터 폴더]", file=sys.stderr)
        sys.exit(2)
    if len(sys.argv) == 2:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = DEFAULT_DATA_DIR
    books_path = data_dir / "books.csv"
    loans_path = data_dir / "loans.json"
    report_path = data_dir / "loan_report.csv"

    # 7장에서는 메시지를 출력하고 return했다. 그러면 프로그램이 실패했는데도
    # 종료 코드가 0(성공)이 된다. 이제는 시작하지 못하는 이유를 표준 오류로
    # 알리고 sys.exit(1)로 끝내서, 실패했다는 사실을 종료 코드로 남긴다(8.2.2).
    # 표준 오류로 쓰면 표준 출력을 > 로 파일에 돌려도 메시지가 화면에 남는다.
    # sys.exit()는 프로그램을 통째로 끝내므로, 프로그램의 흐름을 책임지는
    # main()에서만 쓴다. 아래쪽 모듈(storage, core)은 예외만 일으킨다.
    try:
        books = load_books(books_path)
    except FileNotFoundError:
        print(f"도서 목록 파일이 없습니다: {books_path}", file=sys.stderr)
        sys.exit(1)
    except DataFileError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    library = Library(books)
    try:
        load_loans(library, loans_path)
    except DataFileError as e:
        print(e, file=sys.stderr)
        print(
            "파일을 고친 뒤 다시 실행하세요. 기록을 지키기 위해 프로그램을 시작하지 않습니다.",
            file=sys.stderr,
        )
        sys.exit(1)

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
                # 기록이 남는다(실습 7-4 요구 사항 7). 저장하는 도중에 끊기면 "w"로 이미
                # 지운 파일이 비거나 반만 쓰인 채 남을 수 있다(7장 "더 해 보기"의 안전하게 저장하기 참고).
                save_loans(library, loans_path)
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
                save_loans(library, loans_path)
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

        elif command == "대출자":
            if len(args) != 0:
                print("형식: 대출자")
                continue
            print_lines(library.borrower_lines(), "대출 중인 도서가 없습니다.")

        elif command == "도서":
            if len(args) != 0:
                print("형식: 도서")
                continue
            print_lines(library.book_lines(), "소장 도서가 없습니다.")

        elif command == "보고서":
            if len(args) != 0:
                print("형식: 보고서")
                continue
            count = write_report(library, report_path, today)
            print(f"대출 {count}건을 저장했습니다: {report_path}")

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


# python -m library.cli로 실행할 때만 main()을 호출한다. main.py나 __main__.py가
# 이 모듈을 import할 때는 호출하지 않는다(8.1.5). python library/cli.py로
# 실행하면 이 줄에 오기 전에 첫 import에서 ModuleNotFoundError가 난다(8.3.4).
if __name__ == "__main__":
    main()
