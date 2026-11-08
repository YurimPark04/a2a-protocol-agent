import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage

from state import ExpenseState
from tools import ALL_TOOLS, check_policy

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


# LOOP 와 유사한 개념
# MAX_STEPS = 1
MAX_STEPS = 6

# CHECK_POLICY는 비즈니스 로직에서 관리를 해야 하므로 제외
planner = model.bind_tools([t for t in ALL_TOOLS if t.name != "check_policy"])
by_name = {t.name: t for t in ALL_TOOLS}  # 도구를 이름으로 찾는다


# 무엇을 가지고 올지 정하는 노드
def plan(state: ExpenseState) -> dict:
    msgs = state.get("messages") or [HumanMessage(
        f"출장 {state['trip_id']}의 영수증을 가져오세요. "
        "외화로 된 항목이 있으면 그 통화의 환율도 가져오세요. "
        "필요한 자료를 다 모았으면 도구를 더 부르지 말고 '완료'라고만 답하세요."
    )]
    ai = planner.invoke(msgs)
    new = msgs + [ai] if not state.get("messages") else [ai]
    return {"messages": new, "steps": state.get("steps", 0) + 1}  # STEP 증가


# 도구 호출을 위한 함수 작성 
def run_tools(state: ExpenseState) -> dict:
    ai = state["messages"][-1]
    out = {"messages": [], "log": []}
    
    for tc in ai.tool_calls:
        result = by_name[tc["name"]].invoke(tc["args"])
        out["messages"].append(ToolMessage(content=str(result), tool_call_id=tc["id"])) # tool_call_id를 맞춰야 한다. (어느 답이 어느 요청건인지 매칭)
        out["log"].append(f"{tc['name']}({tc['args']}) 호출")
        if tc["name"] == "list_receipts":
            out["receipts"] = result
        elif tc["name"] == "get_rate":
            rates = dict(state.get("rates") or {})
            rates[tc["args"]["currency"].upper()] = result
            out["rates"] = rates
    return out


# 파이썬 비즈니스 로직 
def compute(state: ExpenseState) -> dict:
    # receipts = state["receipts"]  # 모든 영수증 확인
    # rates = state["rates"]

    # 상한을 걸어두면, 상한이 걸린 다음 경로로 돌아야 함
    receipts = state.get("receipts") or []  # state 가 있을 수 있고, 없을 수도 있다를 가정한 상태로 진행
    rates = state.get("rates") or {}
    total = 0
    violations = []
    for r in receipts:
        cur = r.get("currency", "KRW")
        krw = r["amount"] if cur == "KRW" else r["amount"] * rates.get(cur, 0)
        total += krw
        verdict = check_policy.invoke({"item": r["item"], "amount": krw})
        if "넘습니다" in verdict:
            violations.append(verdict)
    return {"total": total, "violations": violations,
            "log": [f"영수증 {len(receipts)}건으로 원화 합계 {total}원 계산",
                    f"규정 위반 {len(violations)}건"]}


# 밖으로 보여주고자 하는 문장
def escalate(state: ExpenseState) -> dict:
    report = (
        f"출장 {state['trip_id']}의 원화 합계는 {state['total']}원입니다. "
        "규정 위반이 있어 사람 승인이 필요합니다."
    )
    return {"report": report, "log": ["승인 필요"]}



# 파이썬 비즈니스 로직이 만들어낸 결과만 넘긴다. 
def summarize(state: ExpenseState) -> dict:
    prompt = (
        f"출장 {state['trip_id']}의 원화 합계는 {state['total']}원이고 규정 위반은 없습니다.\n"
        "위 사실만 써서 한국어 한 문장으로 보고하세요. 숫자를 바꾸지 마세요."
    )
    return {"report": model.invoke(prompt).content.strip(), "log": ["보고 작성"]}



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


# def summarize(state: ExpenseState) -> dict:
#     lines = "\n".join(f"- {r['item']}: {r['amount']}원" for r in state["receipts"])  # 영수증 항목을 한 줄씩 나열
#     prompt = (
#         f"출장 {state['trip_id']}의 경비 내역입니다.\n"
#         f"{lines}\n"
#         f"합계는 {state['total']}원입니다.\n"
#         "이 내역을 한국어 한 문장으로 요약하세요. 숫자는 주어진 값을 그대로 쓰세요."
#     )
#     answer = model.invoke(prompt)  # 모델 호출 (응답 객체는 content 속성에 실제 답변이 들어있다. strip-> 공백 제거)
#     return {"report": answer.content.strip(), "log": ["요약 작성"]}




"""
# docker compose exec app python -c "import sys; sys.path.insert(0, 'src'); from nodes import collect, tally; s = collect({'trip_id': 'T-2026-03'}); print(s); print(tally({'receipts': s['receipts']}))"

# {'receipts': [{'item': '항공권', 'amount': 820000}, {'item': '호텔', 'amount': 540000}, {'item': '식비', 'amount': 43000}], 'log': ['영수증 3건 수집']}
# {'total': 1403000, 'log': ['합계 1403000원 계산']}


"""


"""
모델이 하는 역할

1. 다음에 무엇을 가지고 오는가
2. 다 모였을 때, 언제 중단하는가?
    - 값을 만들고 검증하는 건 비즈니스 로직으로 (모델이 위임할 부분은 x)


"""