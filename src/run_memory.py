from langgraph.checkpoint.memory import MemorySaver

from graph import build_graph

saver = MemorySaver() # 메모리에 값을 담고, (DB가 없어도, 이 checkpointer를 사용할 수 있음)
graph = build_graph(checkpointer=saver)

# thread_id : 실행 단위의 이름값
# checkpointer는 thread_id라는 이름을 기준으로 상태값을 기록
# checkpointer가 필요한 이유?: 실행이 여러개이기 때문에, thread_id 가 필요함 (T-2026-03 라는 실행이 독립적인 자기 상태를 가지고 있어야 한다)
# config = {"configurable": {"thread_id": "trip-3"}}  # configurable를 객체 형태로 만듦

# result = graph.invoke({"trip_id": "T-2026-03", "messages": [], "log": [], "steps": 0}, config)  # config 추가
# print("1회차 합계:", result["total"])

# snapshot = graph.get_state(config)
# print("저장된 합계:", snapshot.values["total"])
# print("저장된 메시지 수:", len(snapshot.values["messages"]))
# print("다음에 갈 노드:", snapshot.next)  # 다음에 갈 노드

# for snap in graph.get_state_history(config):
#     print(snap.metadata.get("step"), snap.next, snap.values.get("total"))
# get_state_history -> 최신부터 거꾸로 이력을 다 담아서 준다. 
# 메모리 세이버는 프로세스 안에만 있다 보니까, 이력 자체를 보려면 같은 실행 안에서 봐야 함.
    # 파일 하나에 실행과 조회 다 넣어야 함 - 메모리 세이버의 한계
    # 이 부분이 A2A와 어떻게 활용되는가? - task_id 를 기반으로 실행에 연결


# trip-3: {}
# trip-9: {}
# 같은 그래프에 다른 이름을 준다면 (thread-id를 다르게 준다면?) - 두 실행 상태값들이 모두 비워짐
    # 메모리 세이버를 새로 만듦 (앞에서 저장한 건 다른 프로세스. 서로 다른 프로세스임)
    # A 프로세스에 남아있는 값은 A 프로세스에서 선언한 메모리 세이버는 A 프로세스가 끝났을 때 소멸됨

import sys; sys.path.insert(0, 'src')
from langgraph.checkpoint.memory import MemorySaver
from graph import build_graph

graph = build_graph(checkpointer=MemorySaver())
print('trip-3:', graph.get_state({'configurable': {'thread_id': 'trip-3'}}).values)
print('trip-9:', graph.get_state({'configurable': {'thread_id': 'trip-9'}}).values)



"""

> C:\studyhub\ai\agentic-ai\a2a-protocol>docker compose exec app python src/run_memory.py
 
1회차 합계: 2483000
저장된 합계: 2483000
저장된 메시지 수: 5
다음에 갈 노드: ()  # 잘 종료됨 - 중간에 멈췄다면, 다음에 갈 노드이름이 들어감
5 () 2483000
4 ('escalate',) 2483000
3 ('compute',) None
2 ('plan',) None
1 ('tools',) None
0 ('plan',) None
-1 ('__start__',) None



get_state가 실행이 된다.



"""