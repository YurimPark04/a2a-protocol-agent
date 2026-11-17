import os

from langgraph.checkpoint.postgres import PostgresSaver

from graph import build_graph

# with로 감싼 이유: from_conn_string 은 context manager를 돌려주기 때문에 with 가 필요
# with 블록을 벗어나면 DB 연결이 종료됨 
# with 구문 밖에서 그래프를 쓰면 안됨
with PostgresSaver.from_conn_string(os.environ["POSTGRES_URL"]) as saver:
    saver.setup() # relation "checkpoints" does not exist 
    # setup -> 테이블을 만들어주는 것
    graph = build_graph(checkpointer=saver)
    config = {"configurable": {"thread_id": "trip-3"}}

    result = graph.invoke({"trip_id": "T-2026-03", "messages": [], "log": [], "steps": 0}, config)
    print("합계:", result["total"])

"""
> docker compose exec app-2 python src/run_pg.py


합계: 2483000


"""