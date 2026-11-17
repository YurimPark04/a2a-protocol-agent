import os

from langgraph.checkpoint.postgres import PostgresSaver

from graph import build_graph

# 조회
# 주의: setup() 필요 없음 - 이미 테이블은 run_pg 파일에서 실행되어 만들어져 있음 
with PostgresSaver.from_conn_string(os.environ["POSTGRES_URL"]) as saver:
    graph = build_graph(checkpointer=saver)
    config = {"configurable": {"thread_id": "trip-3"}}

    snapshot = graph.get_state(config)
    if not snapshot.values:
        print("저장된 상태 없음")
    else:
        print("합계:", snapshot.values["total"])
        print("위반:", len(snapshot.values["violations"]), "건")
        print()
        print("체크포인트 이력 (최신부터):")
        for snap in graph.get_state_history(config):
            step = snap.metadata["step"]
            nxt = snap.next or ("끝",)
            print(f"  step {step:>2} · 다음 노드 {nxt}")

# next 라는 필드가 매우 중요하다. 
# next 라는 필드? 여기서 멈춘다면 다음에 어디로 가야 하는가?에 대한 정보가 들어있음
    # 앞에서 멈췄다 이어갈려면 어디서 멈춘건지도 알아야 함
    # a2a task 구현할 때, 이 부분을 그대로 활용함

# 우리가 지정한 볼륨만 저장된다면, 컨테이너 재실행해도 데이터들은 다 살아있음
"""

> docker compose exec app-2 python src/show_history.py


* MemorySaver 와는 달리, 다른 프로세스임에도 불구하고 상태가 잘 나왔음을 확인할 수 있음

합계: 2483000
위반: 1 건

체크포인트 이력 (최신부터):
  step  5 · 다음 노드 ('끝',)
  step  4 · 다음 노드 ('escalate',)
  step  3 · 다음 노드 ('compute',)
  step  2 · 다음 노드 ('plan',)
  step  1 · 다음 노드 ('tools',)
  step  0 · 다음 노드 ('plan',)
  step -1 · 다음 노드 ('__start__',)

"""