import sys
from graph import build_graph

trip = sys.argv[1] if len(sys.argv) > 1 else "T-2026-03"
graph = build_graph()

# for chunk in graph.stream({"trip_id": "T-2026-03", "log": []}):
#     for node, update in chunk.items():
#         print(f"[{node}] {update}")


# 외화가 섞여있는 데이터부터 돌린다. 
for chunk in graph.stream({"trip_id": trip, "messages": [], "log": [], "steps": 0}):
    for node, update in chunk.items():
        if node == "plan":
            ai = update["messages"][-1]
            calls = [c["name"] for c in ai.tool_calls] or "없음"
            print(f"[plan] 스텝 {update['steps']} · 도구 요청: {calls}")
        elif node == "tools":
            print(f"[tools] {update['log']}")
        elif node == "compute":
            print(f"[compute] 합계 {update['total']} · 위반 {len(update['violations'])}건")
        else:
            print(f"[{node}] {update['report'][:60]}...")



"""
> docker compose exec app python src/run_stream.py T-2026-03

------------ [결과물] -------------------
[plan] 스텝 1 · 도구 요청: ['list_receipts', 'get_rate']
[tools] ["list_receipts({'trip_id': 'T-2026-03'}) 호출", "get_rate({'currency': 'USD'}) 호출"]
[plan] 스텝 2 · 도구 요청: 없음
[compute] 합계 2483000 · 위반 1건
[escalate] 출장 T-2026-03의 원화 합계는 2483000원입니다. 규정 위반이 있어 사람 승인이 필요합니다....
---------------------------------------------------------



> docker compose exec app python src/run_stream.py T-2026-04

------------ [결과물] -------------------
[plan] 스텝 1 · 도구 요청: ['list_receipts', 'get_rate']
[tools] ["list_receipts({'trip_id': 'T-2026-04'}) 호출", "get_rate({'currency': 'USD'}) 호출"]
[plan] 스텝 2 · 도구 요청: 없음
[compute] 합계 50000 · 위반 0건
[summarize] 출장 T-2026-04의 원화 합계는 50000원이며, 규정 위반은 없습니다....
---------------------------------------------------------

** 위반 건에 대해서는 escalate 가, 위반이 없던 건에 대해서는 summarize 가 호출


RECEIPTS = {
    "T-2026-03": [
        {"item": "항공권", "amount": 820000, "currency": "KRW"},
        {"item": "호텔", "amount": 1200, "currency": "USD"},
        {"item": "식비", "amount": 43000, "currency": "KRW"},
    ],
    "T-2026-04": [
        {"item": "택시", "amount": 32000, "currency": "KRW"},
        {"item": "식비", "amount": 18000, "currency": "KRW"},
    ],
}

* KRW 인데도 get_rate를 호출
* 이유?
* [plan] 스텝 1 · 도구 요청: ['list_receipts', 'get_rate'] 
  - 도구 2개를 한번에 요청: 영수증은 아직 확인은 안하고, 환율을 계산하는 것까지 같이 부른 것 (짐작하고 판단한 것)
  - compute 라는 함수가 원화 항목에서는 환율 데이터를 안쓴다. 합계값은 달라지는게 없음
  - 짚고 넘어가야 할건, 모델을 100프로 신뢰할수는 없다 (모델이 정하는 건 엇갈릴 수 있다)
  - 오늘은 도구를 한번 부르는 걸로 끝낼 수는 있으나, 다른 요청에서는 필요없는 도구도 부를 수 있다
    - 필요한데 안부를 수도 있지 않나라는 관점으로 생각해볼만한 부분

"""


"""
* summarize 는 ollama를 호출하기 때문에 시간이 오래걸렸다.
* docker compose exec app python src/run_stream.py

- 노드가 끝날때마다 한개씩 결과값을 확인할 수 있고
- 그 키값이 노드 이름, 노드가 돌려준 결과값으로 구성


결과물 (단순하게 노드가 자기가 바꾼것만 돌려줌)
[collect] {'receipts': [{'item': '항공권', 'amount': 820000}, {'item': '호텔', 'amount': 540000}, {'item': '식비', 'amount': 43000}], 'log': ['영수증 3건 수집']}
[tally] {'total': 1403000, 'log': ['합계 1403000원 계산']}
[summarize] {'report': '출장 T-2026-03의 경비는 항공권 820,000원, 호텔 540,000원, 식비 4,300원 등으로 총 1,403,000원입니다.', 'log': ['요약 작성']}


* Insights
1. stream 이 나중에 가면 중요한 개념일 수도 있음 
  - 에이전트가 오래걸리는 경우가 대부분인데, 부르는 쪽이 그정도로 기다리기가 매우 어렵다
  - 요청을 했는데 답변이 안오는 상황 (클라이언트 입장에서는)

2. 우리 프로세스 안에서는 보기만 하면 되는데, 나중에는 이 값을 네트워크 너머로 보내줘야 한다. 
  - a2a 입장에서는 새 요청을 보내면, 받는 값과 기존 task 에 다시 붙여야 하는 그 값에 역할을 나누어 보아야 한다


*** 더 복잡하게 만드려면(도메인에 따라서 분기처리), 도구를 붙여야 하고, 모델이 어떤 도구를 부르냐를 고르게 해야 하고, 
  *** 그 결과에 따라서 값이 갈리게 만들어야 함
*** 그래프의 흐름을 어떻게 익힌 다음에 상태를 받도록 저장하는 패턴을 익혀야 함



[[섹션2]]
1. 상태 정의, 리듀서 패턴을 기반으로 값을 덮을 건지 쌓을 건지 구분할 수 있고
2. 노드는 생각해보면 일반 함수이고, return 문은 단순한 dict만 return 해준다
3. 노드 add, 엣지 추가 


`TypedDict`와 리듀서(Reducer)를 활용하여 상태를 관리하는 것이 LangGraph의 핵심 구성 요소 중 하나로 소개되었습니다.
A2A 프로토콜의 태스크 상태 관리와 연계하여 노드, 엣지, 상태로 구성된 그래프 기반 에이전트 아키텍처를 설계하는 방법을 다뤘습니다.





"""