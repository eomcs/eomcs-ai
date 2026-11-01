# 3장 실습 3-7 해답 — 편의점 계산대 프로그램
#
# ch03.md의 "실습 3-7. 종합"의 요구 사항을 3장까지 배운 문법만으로
# 구현한 것이다. 함수(4장)와 예외 처리(6장) 없이 리스트·튜플·딕셔너리·집합과
# 2장의 조건문·반복문만 사용한다.

# 상품 코드로 상품을 찾아야 하므로 "코드를 키로 하는 딕셔너리"다(3.6.3 모양 2).
# 프로그램 안에서 바꾸지 않을 값이므로 이름을 대문자로 쓴다.
PRODUCTS = {
    "A01": {"name": "삼각김밥", "price": 1500, "category": "식품"},
    "A02": {"name": "컵라면", "price": 1800, "category": "식품"},
    "B01": {"name": "생수", "price": 1000, "category": "음료"},
    "B02": {"name": "커피", "price": 2500, "category": "음료"},
    "C01": {"name": "볼펜", "price": 1200, "category": "문구"},
}

# 장바구니: {상품코드: 수량}
# 상품 정보를 복사해 넣지 않고 코드와 수량만 저장한다. 이름과 가격은
# 필요할 때 PRODUCTS에서 꺼내 읽기만 하므로 PRODUCTS가 바뀔 일이 없다(요구 사항 7).
# 딕셔너리는 넣은 순서를 기억하므로(3.4.1) 처음 담은 순서가 그대로 유지된다.
cart = {}

# ---------------------------------------------------------------------------
# 1. 입력 받기
# ---------------------------------------------------------------------------
while True:
    line = input("상품코드 수량 (끝내려면 Enter): ")

    # split()은 앞뒤와 사이의 공백을 모두 무시하고 나누므로(2.3.5)
    # 공백만 입력해도 빈 리스트가 된다. 빈 리스트는 거짓이다(2.4.5).
    words = line.split()
    if not words:
        break

    # 단어 개수를 먼저 확인한 뒤에 언패킹한다(3.3.3).
    # 순서가 반대면 "C01"처럼 한 단어만 입력했을 때 ValueError가 난다.
    if len(words) != 2:
        print("  형식: 상품코드 수량 (예: A01 2)")
        continue
    code, quantity_text = words

    # 상품 코드는 대소문자를 구분하지 않는다(요구 사항 2).
    # 문자열 메서드는 원본을 바꾸지 않으므로 결과를 다시 할당한다(2.3.5).
    code = code.upper()

    # 딕셔너리에서 in은 키를 검사한다(3.4.2).
    # 없는 코드로 PRODUCTS[code]를 꺼내면 KeyError가 나므로 먼저 확인한다.
    if code not in PRODUCTS:
        print(f"  없는 상품 코드입니다: {code}")
        continue

    # isdecimal()이 참일 때만 int()를 계산한다. and는 왼쪽이 거짓이면
    # 오른쪽을 계산하지 않으므로 "두개"나 "²"가 int()에 들어가지 않는다.
    # "0"도 isdecimal()은 참이므로 1 이상인지 따로 검사한다.
    if not (quantity_text.isdecimal() and int(quantity_text) >= 1):
        print("  수량은 1 이상의 정수로 입력하세요.")
        continue
    quantity = int(quantity_text)

    # 개수 세기 패턴(3.4.5)과 같은 모양이다. 처음 담는 상품이면
    # get()이 0을 돌려주므로 KeyError 없이 수량이 저장된다.
    already_in_cart = code in cart
    cart[code] = cart.get(code, 0) + quantity

    name = PRODUCTS[code]["name"]
    if already_in_cart:
        print(f"  → {name} {quantity}개 담음 (현재 {cart[code]}개)")
    else:
        print(f"  → {name} {quantity}개 담음")

# ---------------------------------------------------------------------------
# 2. 영수증 출력
# ---------------------------------------------------------------------------
# 빈 딕셔너리는 거짓이다(2.4.5).
if not cart:
    print("구매한 상품이 없습니다.")
else:
    total_price = 0
    total_quantity = 0
    categories = set()  # 빈 집합은 {}가 아니라 set()이다(3.5.1)

    print("=" * 10, "영수증", "=" * 10)

    # items()가 내놓는 (키, 값) 튜플을 바로 언패킹한다(3.4.4).
    for code, quantity in cart.items():
        # 중간 단계에 이름을 붙인다(3.4.6). 복사가 아니라 이름표를
        # 하나 더 붙인 것이므로(3.2.2) 비용이 들지 않는다.
        product = PRODUCTS[code]
        subtotal = product["price"] * quantity
        print(f"{product['name']} {product['price']:,}원 x {quantity} = {subtotal:,}원")

        total_price += subtotal
        total_quantity += quantity
        # 같은 분류를 여러 번 add()해도 하나만 남는다(3.5.2).
        categories.add(product["category"])

    print("-" * 28)
    # 상품 종류 수는 장바구니의 키 개수와 같다.
    print(f"총 수량: {total_quantity}개 ({len(cart)}종류)")
    print(f"합계: {total_price:,}원")
    # 집합은 순서가 없으므로 sorted()로 가나다순 리스트를 만든 뒤 잇는다.
    print(f"구매 분류: {', '.join(sorted(categories))}")
    print("=" * 28)


# ---------------------------------------------------------------------------
# "확인할 것" 참고 답
#
# 1. 아무것도 담지 않고 바로 Enter를 누르면 첫 바퀴에서 반복이 끝나고,
#    cart가 빈 딕셔너리이므로 "구매한 상품이 없습니다."만 출력된다.
#
# 2. 입력에 대한 동작
#    A01 0     : isdecimal()은 참이지만 int("0") >= 1이 거짓이다.
#                "수량은 1 이상의 정수로 입력하세요."
#    A01 -1    : "-"는 십진수 숫자가 아니므로 isdecimal()이 거짓이다. 같은 메시지.
#    A01 ²     : "²".isdecimal()이 거짓이므로 int()까지 가지 않는다. 같은 메시지.
#                isdigit()으로 검사했다면 "²"가 통과해 int("²")에서
#                ValueError가 나고 프로그램이 멈춘다.
#    A01 2 3   : 단어가 3개이므로 "형식: 상품코드 수량 (예: A01 2)"
#     a01   2  : split()이 공백을 모두 처리하므로 ["a01", "2"]가 되고,
#                upper()로 A01이 되어 삼각김밥 2개가 정상적으로 담긴다.
#    모두 요구 사항대로 동작한다.
#
# 3. 영수증 뒤에 print(PRODUCTS)를 추가하면 처음과 같은 내용이 출력된다.
#    이 해답은 장바구니에 코드와 수량만 저장하고, PRODUCTS의 값은
#    product["price"]처럼 읽기만 하기 때문이다.
#    만약 장바구니에 cart[code] = PRODUCTS[code]처럼 상품 딕셔너리를 넣고
#    cart[code]["qty"] = quantity 식으로 수량을 기록했다면, cart[code]와
#    PRODUCTS[code]가 같은 딕셔너리 객체이므로(3.2.2) PRODUCTS에도 "qty"가
#    생긴다. PRODUCTS[code].copy()로 바깥 딕셔너리를 복사하면 이 경우는
#    막을 수 있지만, 상품 정보 안에 리스트 같은 가변 객체가 있다면 얕은
#    복사로는 부족하다(3.2.5). 코드와 수량만 저장하는 쪽이 가장 단순하고 안전하다.
#
# 4. 디버거: cart[code] = ... 줄의 다음 줄에 중단점을 찍고 F5를 누를 때마다
#    변수 패널의 cart를 펼쳐 보면, 실행 예의 입력에서
#    {'A01': 2} → {'A01': 2, 'B02': 1} → {'A01': 3, 'B02': 1}
#    순서로 바뀌는 것을 볼 수 있다. 잘못된 입력은 continue로 이 줄에
#    도달하지 않으므로 cart가 바뀌지 않는다.
# ---------------------------------------------------------------------------
