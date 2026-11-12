"""거래 목록을 요약하는 계산.

파일도 화면도 모른다. models만 가져온다.
"""

from collections import defaultdict

from ledger.models import Summary, Transaction


def summarize(transactions: list[Transaction]) -> Summary:
    """거래 목록을 요약한 Summary를 돌려준다.

    지출은 분류별로 합쳐 금액이 큰 순(같으면 분류 이름 순)으로 정렬한다.
    거래가 하나도 없으면 ValueError를 일으킨다.
    빈 목록인지는 호출하는 쪽이 먼저 확인한다.
    """
    if not transactions:
        raise ValueError("요약할 거래가 없습니다")

    income = 0
    expense = 0
    by_category = defaultdict(int)  # {분류: 금액}
    for t in transactions:
        if t.kind == "수입":
            income += t.amount
        else:
            expense += t.amount
            by_category[t.category] += t.amount

    ranked = sorted(by_category.items(), key=lambda item: (-item[1], item[0]))
    first = min(transactions, key=lambda t: t.day)
    last = max(transactions, key=lambda t: t.day)
    return Summary(
        count=len(transactions),
        first_day=first.day,
        last_day=last.day,
        income=income,
        expense=expense,
        expense_by_category=ranked,
    )
