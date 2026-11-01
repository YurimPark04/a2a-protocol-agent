import os
from langchain_ollama import ChatOllama


from state import ExpenseState

# 간단한 상수값 선언
# 영수증 데이터를 딕셔너리에 하드코딩
# 외부에서 호출해야 하는 데이터
RECEIPTS = {
    "T-2026-03": [
        {"item": "항공권", "amount": 820000},
        {"item": "호텔", "amount": 540000},
        {"item": "식비", "amount": 43000},
    ],
}

model = ChatOllama(
    model="qwen2.5:3b",
    base_url=os.environ.get("OLLAMA_URL"),  # docker - compose.yaml 의 키값을 읽는다는 의미
    temperature=0,   # 답변에 대한 다양성을 줄이는 것. 0이면 항상 같은 답변을 내놓는다. 1이면 다양하게 내놓는다. (비결정적인 요소를 최대한 낮추기 위해서)
    # 보장한다는 의미는 아님. 비결정적인 요소는 불가피하지만, 많이 차이 나지는 않는다
)


# 노드 3개 - 3개 모두 state를 받는다. 
# 자신이 새로 만든 값만 return 한다. (받는다 - > 계산한다 -> return 한다)
def collect(state: ExpenseState) -> dict:
    receipts = RECEIPTS.get(state["trip_id"], [])  # 번호에 맞는 id를 가져온다. 없으면 빈 리스트를 가져온다.
    return {"receipts": receipts, "log": [f"영수증 {len(receipts)}건 수집"]}


# 합계는 모델이 계산하지 않고, 단순히 합계를 계산하는 노드이다.
# 비결정성인 특성 - 산수가 틀릴 수 있다 (매번 다른 결과 -> 신뢰성 저하)
# 계산과 판단을 가른다. 계산은 deterministic 해야 한다. 판단은 비결정적이어도 된다.
# 계산은 파이썬. 모델은 무엇을 계산할지 고르거나, 그 결과를 언어로 해석할때 활용한다.
# 도구가 값을 만들고, 모델은 어떤 도구를 쓸지 판단하는 역할을 한다. (모델은 계산을 하지 않는다)
def tally(state: ExpenseState) -> dict:
    total = sum(r["amount"] for r in state["receipts"])  # 앞 노드에서 받은 영수증 리스트를 사용하여 합계를 계산
    return {"total": total, "log": [f"합계 {total}원 계산"]}


def summarize(state: ExpenseState) -> dict:
    lines = "\n".join(f"- {r['item']}: {r['amount']}원" for r in state["receipts"])  # 영수증 항목을 한 줄씩 나열
    prompt = (
        f"출장 {state['trip_id']}의 경비 내역입니다.\n"
        f"{lines}\n"
        f"합계는 {state['total']}원입니다.\n"
        "이 내역을 한국어 한 문장으로 요약하세요. 숫자는 주어진 값을 그대로 쓰세요."
    )
    answer = model.invoke(prompt)  # 모델 호출 (응답 객체는 content 속성에 실제 답변이 들어있다. strip-> 공백 제거)
    return {"report": answer.content.strip(), "log": ["요약 작성"]}


"""
# docker compose exec app python -c "import sys; sys.path.insert(0, 'src'); from nodes import collect, tally; s = collect({'trip_id': 'T-2026-03'}); print(s); print(tally({'receipts': s['receipts']}))"

# {'receipts': [{'item': '항공권', 'amount': 820000}, {'item': '호텔', 'amount': 540000}, {'item': '식비', 'amount': 43000}], 'log': ['영수증 3건 수집']}
# {'total': 1403000, 'log': ['합계 1403000원 계산']}


"""