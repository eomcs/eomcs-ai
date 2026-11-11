"""8장 실습 8-4 해답 — 도서 대출 관리 프로그램(패키지 버전)의 시작 파일.

ch08.md의 "실습 8-4. 종합"에 주어진 구조대로, 7장 해답(ch07/library.py)을
library 패키지의 다섯 모듈로 나눈 것이다. 8장까지 배운 문법만 사용한다.

    ch08/
    ├── main.py          이 파일. cli.main()을 불러 호출만 한다
    ├── data/books.csv   7장의 것과 같다
    └── library/
        ├── __init__.py  바깥에 보여 줄 이름을 다시 내보낸다
        ├── __main__.py  python -m library로 실행할 때
        ├── models.py    0층: WEEKDAYS, format_date(), Book, ReferenceBook, Loan
        ├── errors.py    1층: LibraryError와 자식 예외, DataFileError
        ├── core.py      2층: Library (borrower_lines()를 더했다)
        ├── storage.py   3층: load_books(), load_loans(), save_loans(), write_report()
        └── cli.py       4층: DEFAULT_DATA_DIR, HELP_TEXT, print_lines(), parse_days(), main()

실행 방법 (모두 같은 ch08/data의 파일을 읽고 쓴다)
    ch08 폴더에서       python main.py
    python-lab 폴더에서 python ch08/main.py
    ch08 폴더에서       python -m library
    VS Code에서 이 파일을 열고 ▷ 버튼

데이터 폴더를 바꾸려면 python main.py 데이터폴더 (현재 디렉터리 기준)
data/loans.json은 처음 실행할 때는 없어도 되고, 프로그램이 만든다.
"""

# 패키지 바깥에 있는 시작 파일이다. 이 파일을 python main.py나 ▷ 버튼으로
# 실행하면 sys.path의 맨 앞이 ch08이 되므로 library 패키지를 찾을 수 있다(8.3.4).
from library.cli import main

if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# "확인할 것" 참고 답
#
# 1. 실행 예와 같은 결과를 확인하려면 library/cli.py의 today = date.today()를
#    잠시 today = date(2026, 10, 31)로 바꾸고, data/loans.json을 지운 뒤 실행한다.
#
# 2. 네 가지 실행 방법이 모두 같은 파일을 쓰는 이유
#    - python main.py, python ch08/main.py, ▷ 버튼: 스크립트(main.py)가 있는
#      ch08이 sys.path의 맨 앞에 들어가므로 library 패키지를 찾는다(8.1.6).
#    - python -m library: 현재 디렉터리(ch08)가 sys.path의 맨 앞에 들어간다.
#    - 데이터 폴더는 DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"로
#      cli.py의 위치에서 정하므로, 어디서 실행하든 ch08/data다.
#
# 3. python library/cli.py로 실행하면
#        ModuleNotFoundError: No module named 'library'
#    가 난다. 파일 경로로 실행하면 sys.path의 맨 앞이 스크립트가 있는
#    ch08/library 폴더가 되는데, 그 안에는 library라는 패키지가 없다(library는
#    한 단계 위인 ch08에 있다). 예외는 cli.py의 첫 번째 from library... 줄에서
#    나므로 맨 아래의 if __name__ == "__main__":까지 가지도 못한다.
#    python -m library.cli는 현재 디렉터리(ch08)를 검색 경로에 넣고 모듈 이름으로
#    찾으므로 된다. 이때 cli의 __name__은 "__main__"이므로 main()이 호출된다.
#    VS Code의 ▷ 버튼은 python 파일경로로 실행하므로 python library/cli.py와 같다.
#
# 4. import 줄로 그린 층 그림 (화살표는 "가져온다")
#        main.py → cli
#        cli     → storage, core, errors, models
#        storage → core, errors, models
#        core    → errors, models
#        errors  → models
#        models  → (없음)
#    아래층이 위층을 가져오는 화살표는 없다. core.py의 import는 collections,
#    datetime, library.errors, library.models뿐이고 csv, json, pathlib, storage는 없다.
#
# 5. models.py에 from library.errors import LibraryError를 넣고 실행하면
#    트레이스백은 main.py → library/__init__.py → core.py → errors.py → models.py
#    순서로 나오고, 맨 아래 줄은
#        ImportError: cannot import name 'LibraryError' from partially initialized
#        module 'library.errors' (most likely due to a circular import)
#    다. 8.1.8의 패키지가 아닌 모듈과 달리, 패키지 안의 모듈에서는 3.13도
#    "덜 만들어진 모듈", "순환 import"라고 정확히 알려 준다.
#    main.py는 library.cli를 가져오지만, 패키지 안의 모듈을 하나라도 가져오면
#    패키지의 __init__.py가 먼저 실행된다(8.3.2). __init__.py가 core를 가져오고,
#    core가 errors를, errors가 models를, models가 다시 errors를 가져오는데
#    errors는 첫 import 줄을 실행하던 중이라 LibraryError가 아직 없다.
#
# 6. 셸에서 from library import Library를 해도 main()이 실행되지 않는 이유:
#    __init__.py는 cli를 가져오지 않는다. 설령 cli를 가져오더라도 cli.py의
#    main() 호출은 if __name__ == "__main__": 안에 있고, import될 때 cli의
#    __name__은 "library.cli"이므로 호출되지 않는다(8.1.5).
#
# 7. test_data 폴더로 실험하기
#        ch08에서 mkdir test_data, data/books.csv를 test_data에 복사
#        python main.py test_data
#    test_data/loans.json을 망가뜨려도 data/loans.json은 그대로다. 7장의
#    오류 메시지가 그대로 나오고, 시작하지 못한 경우의 종료 코드는 1이다.
#    인자를 두 개 주면(python main.py a b) 사용법이 나오고 종료 코드는 2다.
#
# 8. python main.py test_data > out.txt
#    - loans.json이 망가졌을 때: 오류 메시지는 표준 오류로 나가므로 화면에
#      보이고, out.txt는 비어 있다(표준 출력으로 아무것도 쓰기 전에 끝났다).
#    - 정상일 때: 시작 안내, 프롬프트 "> ", 명령 결과가 모두 out.txt로 간다.
#      input()의 안내 문구도 표준 출력이기 때문이다. 화면에는 아무것도 보이지
#      않지만 키보드 입력은 그대로 받으므로 종료를 입력하면 끝난다.
#
# 9. __init__.py를 비워도 python main.py는 동작한다. main.py는 library.cli를,
#    cli.py는 library.core 같은 하위 모듈을 직접 가져오기 때문이다.
#    다시 내보내기는 패키지를 쓰는 바깥 사람(셸에서 시험하는 사람, 이 패키지를
#    가져다 쓰는 다른 프로그램)을 위한 것이다. 비우면 from library import
#    Library가 ImportError를 낸다.
#
# 10. 변경할 때 고칠 파일
#    (가) 대출 기간 14일 → 21일: core.py의 Library.LOAN_DAYS 한 곳
#    (나) JSON 대신 JSONL로 저장: storage.py의 load_loans(), save_loans()
#         (cli.py의 loans_path 파일 이름도 바꾼다면 cli.py까지)
#    (다) 목록 → 대출목록: cli.py의 main()과 HELP_TEXT
#    (라) 7일만 빌려주는 신간 도서: models.py(새 클래스와 대출 기간을 알려 줄
#         방법), core.py(borrow()가 도서마다 다른 기간을 쓰게), storage.py
#         (books.csv의 kind에 '신간'을 읽게)를 모두 고쳐야 한다. 도서의 종류라는
#         데이터, 대출 기간이라는 규칙, 파일 형식이 함께 바뀌는 변경이라서
#         여러 층에 걸친다. 그래도 고칠 곳이 층별로 나뉘어 있어 찾기는 쉽다.
# ---------------------------------------------------------------------------
