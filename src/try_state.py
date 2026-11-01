from langgraph.graph import StateGraph, START, END
from state import ExpenseState


# 노드 2개 -  total 은 덮어씌우고, log는 합쳐서 출력되도록 한다.
def first(state: ExpenseState) -> dict:
    return {"total": 100, "log": ["first가 씀"]}

def second(state: ExpenseState) -> dict:
    return {"total": 200, "log": ["second가 씀"]}

# 그래프 빌드
builder = StateGraph(ExpenseState)

# 노드 등록
builder.add_node("first", first)
builder.add_node("second", second)
# 
builder.add_edge(START, "first")
builder.add_edge("first", "second")
builder.add_edge("second", END)
graph = builder.compile()


result = graph.invoke({"trip_id": "T-2026-03", "log": []})  # 빈 리스트 명시 - list 타입 리듀서의 첫번째 값을 빈 리스트로 시작할 수 있어서, 이 값을 빼도 동작을 한다. 다만 첫 실행에서는 기록이 비어있다는 의미로 넣어둠
print("total:", result["total"]) 
print("log:", result["log"])



"""
1. docker compose exec app python src/try_state.py 
- total: 200 (덮어쓰기)
- log: ['first가 씀', 'second가 씀'] (배열처럼 누적) - 리듀서의 유무에 따라서 달라짐


2. 상태 설계
#  agent, a2a 외부에 공개를 할 때에는 어느 부분을 내보내고 어느 부분을 감춰야할지 정해야 함
#  report는 내보내고 log는 숨긴다. 

# 상태를 하나로 뭉개버리면 나중에 class 필드 하나하나 구분하는게 어렵다. dto 나 entity 의 관점이기도 함
# 상태를 여러개로 나누면, 각 상태마다 어떤 필드를 내보낼지, 어떤 필드를 감출지 정하기가 쉬움
"""