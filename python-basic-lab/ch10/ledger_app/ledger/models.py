"""가계부의 데이터를 나타내는 클래스.

다른 모듈을 가져오지 않는다. 패키지 안에서 가장 아래에 있는 모듈이다.
"""

from dataclasses import dataclass
from datetime import date

KINDS = ("수입", "지출")


@dataclass(frozen=True)
class Transaction:
    """거래 한 건. 파일에서 읽은 뒤에는 바뀌지 않는다."""

    day: date
    kind: str  # "수입" 또는 "지출"
    category: str
    memo: str
    amount: int  # 원 단위, 1 이상

    def __post_init__(self):
        # 타입 힌트는 실행 중에 검사되지 않으므로(5.4.3) 자료형도 직접 검사한다.
        # 불리언은 정수의 자식 클래스라서 isinstance(True, int)가 True다(4.5.3).
        if not isinstance(self.day, date):
            raise TypeError(f"날짜는 date여야 합니다: {self.day!r}")
        if self.kind not in KINDS:
            raise ValueError(f"구분은 '수입'이나 '지출'이어야 합니다: {self.kind!r}")
        if not isinstance(self.category, str) or not isinstance(self.memo, str):
            raise TypeError("분류와 내용은 문자열이어야 합니다")
        if not self.category.strip():
            raise ValueError("분류가 비어 있습니다")
        if not isinstance(self.amount, int) or isinstance(self.amount, bool):
            raise TypeError(f"금액은 정수여야 합니다: {self.amount!r}")
        if self.amount < 1:
            raise ValueError(f"금액은 1 이상이어야 합니다: {self.amount}")


@dataclass
class Summary:
    """거래 목록을 요약한 결과."""

    count: int
    first_day: date
    last_day: date
    income: int
    expense: int
    expense_by_category: list[tuple[str, int]]  # [(분류, 금액), ...] 금액이 큰 순

    @property
    def balance(self) -> int:
        """수입에서 지출을 뺀 금액. 음수일 수 있다."""
        return self.income - self.expense

    def share(self, amount: int) -> float:
        """지출 합계에서 amount가 차지하는 비율(%). 지출이 0이면 0.0이다."""
        if self.expense == 0:
            return 0.0
        return amount / self.expense * 100
