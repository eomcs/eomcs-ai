"""데이터 파일을 읽고 쓰는 함수.

어느 파일을 읽을지는 정하지 않는다. 경로는 호출하는 쪽(cli)이 넘겨준다.
"""

import csv
import json
from datetime import date
from pathlib import Path

# 저장(3층)이 규칙(2층)을 쓰는 것은 허용된 방향이다. 함수의 타입 힌트와
# library.import_loans() 호출에 Library가 필요하다. 반대로 core는 이 모듈을
# 가져오지 않는다. 그래서 Library는 파일을 모른다(8.3.5).
from library.core import Library
from library.errors import DataFileError, LibraryError
from library.models import Book, ReferenceBook


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
    # 파일이 없을 때 할 수 있는 일이 없으므로 main()에 맡긴다(실습 7-4 요구 사항 4).
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
