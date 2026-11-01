from graph import build_graph

graph = build_graph()

for chunk in graph.stream({"trip_id": "T-2026-03", "log": []}):
    for node, update in chunk.items():
        print(f"[{node}] {update}")

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
  - a2a 입장에서는 새 요청을 보내면 받는 값과, 기존 task 에 다시 붙여야 하는 그 값에 역할을 나누어 보아야 한다
  - 
"""