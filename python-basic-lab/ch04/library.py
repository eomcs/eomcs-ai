"""4장 실습 4-7 해답 — 도서 대출 관리 프로그램.

ch04.md의 "실습 4-7. 종합"에 주어진 함수 이름, 매개변수, 독스트링을
그대로 두고 본문을 채운 것이다. 4장까지 배운 문법만 사용한다.
"""

from datetime import date, timedelta

BOOKS = {
    "B01": "파이썬 첫걸음",
    "B02": "데이터 과학 입문",
    "B03": "알고리즘 이야기",
    "B04": "웹 개발 기초",
    "B05": "인공지능 개론",
}
LOAN_DAYS = 14
LATE_FEE_PER_DAY = 100
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

HELP_TEXT = """명령 목록
  대출 도서코드 이름   도서를 대출한다
  반납 도서코드        도서를 반납한다
  목록                 대출 중인 도서를 반납 기한 순으로 보여 준다
  연체                 연체된 도서를 연체일수가 긴 순으로 보여 준다
  날짜 N               오늘 날짜를 N일 뒤로 옮긴다 (시험용)
  도움                 이 목록을 보여 준다
  종료                 프로그램을 끝낸다"""


def format_date(d):
    """날짜를 '2026-11-14(토)' 모양의 문자열로 돌려준다."""
    return f"{d.strftime('%Y-%m-%d')}({WEEKDAYS[d.weekday()]})"


def overdue_days(due, today):
    """반납 기한 due에서 today까지 며칠 지났는지 돌려준다.

    기한이 지나지 않았으면(기한 당일 포함) 0을 돌려준다.
    """
    return max((today - due).days, 0)


def late_fee(days_over, fee_per_day=LATE_FEE_PER_DAY):
    """연체일수 days_over에 따른 연체료(원)를 돌려준다."""
    return days_over * fee_per_day


def borrow(loans, code, who, today, days=LOAN_DAYS):
    """도서를 대출하고, 화면에 출력할 결과 메시지를 돌려준다.

    loans는 {도서코드: {"who": 이름, "due": 반납기한}} 딕셔너리다.
    대출에 성공하면 loans에 항목을 추가한다(원본을 바꾼다).
    반납 기한은 today로부터 days일 뒤다.
    없는 도서 코드이거나 이미 대출 중인 도서이면 loans를 바꾸지 않는다.
    """
    # 실패하는 경우를 먼저 처리하고 바로 돌려준다(조기 반환, 4.1.5).
    if code not in BOOKS:
        return f"없는 도서 코드입니다: {code}"

    title = BOOKS[code]
    if code in loans:
        loan = loans[code]
        due_text = format_date(loan["due"])
        return f"이미 대출 중입니다: '{title}' ({loan['who']}, 반납 기한 {due_text})"

    due = today + timedelta(days=days)
    # 호출할 때마다 새 딕셔너리를 만들어 넣는다(4.3.6).
    loans[code] = {"who": who, "due": due}
    return f"'{title}' 대출 완료 - {who}, 반납 기한 {format_date(due)}"


def return_book(loans, code, today):
    """도서를 반납하고, 화면에 출력할 결과 메시지를 돌려준다.

    반납에 성공하면 loans에서 항목을 지운다(원본을 바꾼다).
    연체되었으면 메시지에 연체일수와 연체료를 포함한다.
    """
    if code not in loans:
        return f"대출 중인 도서가 아닙니다: {code}"

    loan = loans.pop(code)
    title = BOOKS[code]
    days_over = overdue_days(loan["due"], today)
    if days_over == 0:
        return f"'{title}' 반납 완료"
    fee = late_fee(days_over)
    return f"'{title}' 반납 완료 - {days_over}일 연체, 연체료 {fee:,}원"


def loan_lines(loans, today, only_overdue=False):
    """대출 목록을 한 줄에 한 권씩, 문자열의 리스트로 돌려준다.

    기본은 반납 기한이 빠른 순서다(기한이 같으면 도서 코드 순).
    only_overdue가 True이면 연체된 도서만, 연체일수가 긴 순서로 돌려준다.
    연체된 도서는 줄 끝에 '| N일 연체'를 붙인다.
    loans는 바꾸지 않는다.
    """
    # sorted()는 새 리스트를 돌려주므로 loans는 그대로다.
    # 키가 튜플이므로 기한이 같으면 도서 코드로 비교한다(4.5.5).
    items = sorted(loans.items(), key=lambda item: (item[1]["due"], item[0]))

    if only_overdue:
        items = filter(lambda item: overdue_days(item[1]["due"], today) > 0, items)
        # 연체일수 내림차순. 안정 정렬이므로 연체일수가 같으면
        # 바로 위에서 정렬한 순서(기한 → 코드)가 그대로 유지된다.
        items = sorted(items, key=lambda item: -overdue_days(item[1]["due"], today))

    lines = []
    for code, loan in items:
        line = f"{code} {BOOKS[code]} | {loan['who']} | 기한 {format_date(loan['due'])}"
        days_over = overdue_days(loan["due"], today)
        if days_over > 0:
            line += f" | {days_over}일 연체"
        lines.append(line)
    return lines


def main():
    """명령을 반복해서 입력받아 처리한다."""
    loans = {}
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
            print(borrow(loans, code.upper(), who, today))

        elif command == "반납":
            if len(args) != 1:
                print("형식: 반납 도서코드")
                continue
            print(return_book(loans, args[0].upper(), today))

        elif command == "목록":
            if len(args) != 0:
                print("형식: 목록")
                continue
            lines = loan_lines(loans, today)
            if not lines:
                print("대출 중인 도서가 없습니다.")
            for line in lines:
                print(line)

        elif command == "연체":
            if len(args) != 0:
                print("형식: 연체")
                continue
            lines = loan_lines(loans, today, only_overdue=True)
            if not lines:
                print("연체된 도서가 없습니다.")
            for line in lines:
                print(line)

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
# 2. borrow()는 실패하는 두 경우 모두 loans에 손대기 전에 return하므로
#    loans가 바뀌지 않는다. loan_lines()는 sorted()와 filter()만 쓰고
#    loans를 직접 고치는 코드가 없으므로 loans가 바뀌지 않는다.
#
# 3. late_fee()의 기본값 fee_per_day=LATE_FEE_PER_DAY는 def 문이 실행될 때
#    한 번 계산된다(4.2.4). 그 뒤에 LATE_FEE_PER_DAY = 200을 할당해도
#    기본값은 처음의 100 그대로이므로 late_fee(3)은 300이다.
#    바뀐 값을 쓰게 하려면 기본값을 None으로 두고 함수 안에서
#    if fee_per_day is None: fee_per_day = LATE_FEE_PER_DAY 로 정한다.
#
# 4. 대출 기간을 7일로 바꾸려면 LOAN_DAYS = 7 한 군데만 고치면 된다.
#    특정 대출만 7일로 하려면 borrow(loans, code, who, today, days=7)처럼
#    키워드 인자로 기본값을 바꿔 호출한다.
# ---------------------------------------------------------------------------
