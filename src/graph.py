from langgraph.graph import StateGraph, START, END

# 상태 데이터, 노드 import
from nodes import collect, summarize, tally
from state import ExpenseState

# 노드의 실행 순서를 등록
def build_graph():

    # 이 시점에, 리듀서의 존재 유무 등등 사용자가 설정한 각 상태의 타입에 대해서, 인지를 한다
    builder = StateGraph(ExpenseState)   # 빌더를 만들 떄, 상태 타입이 무엇인지를 설정 (우리가 사용하고자 하는, 그래프가 다루는 데이터의 모양이 된다.) + 노드가 돌려준 dict를 어떻게 합치는지도 결정됨. 

    # 노드 등록 - ("이름", 실행 함수)
    # 왜 이름? -> 그래프를 그릴 때, 함수가 아니라, 노드의 이름을 사용해서 연결을 한다. (노드의 이름은 중복되면 안된다.)
        # 이름이 외부에 노출되는 이름이 된다. 만약, 그래프의 단계를 물어본다면, collect, tally, summarize 라는 이름을, 즉 문자값을 본다. 노드가 존재한다는 것을 알 수 있다. (이름은 외부에 공개되는 이름이 된다.)
        # 노출을 해도 되는건지 고민해볼법한 주제..
    builder.add_node("collect", collect)   
    builder.add_node("tally", tally)
    builder.add_node("summarize", summarize)

    # 노드 연결
    builder.add_edge(START, "collect")
    builder.add_edge("collect", "tally")
    builder.add_edge("tally", "summarize")
    builder.add_edge("summarize", END)

    # 등록이 안된 노드를 엣지가 가리킨다 -> 에러 탐지 및 발생
    return builder.compile()  # 빌더 패턴 기반으로 만든 그래프를 컴파일


"""
docker compose exec app python -c "from langgraph.graph import START, END; print(START, END)"

* __start__ __end__
* 어떤 객체가 아니라, 미리 선언해둔 상수값


# 왜 함수화? -> 그래프를 여러번, 다른 설정으로 계속해서 만들게 된다
# 모듈 최상단에서 만들어두면, 파일을 불러오는 시점에 한번만 만들어지는 구조이기 때문에
# 옵셔널한 값을 준다거나, 설정을 바꿔서 실행하고 싶다거나 강의 진행을 하는데에 있어서 번거로울 것 같기 때문에 함수로 감싼 것.
# 인자값들은 추가될 수 있다.
"""