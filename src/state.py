import operator
from typing import Annotated, Any, TypedDict

# 키 - 키의 type
class ExpenseState(TypedDict) :  
    trip_id: str   # 시작할 때 넣는 값
    receipts: list[dict]  # 영수증 목록 -> 첫 번째 노드가 채운다. 
    total: int   # 합계 -> 두번째 노드가 계산
    report: str  # 사람이 읽는 한 줄 (모델이 작성)
    log: Annotated[list[str], operator.add] 

"""
Annotated[list[str], operator.add] 

* 노드는 상태 전체를 돌려주지는 않는다. 자기가 바꾼 부분만 돌려준다.
* 다음에 만들 수집 노드라면, 영수증 목록을 receipts에 추가담아서 돌려준다 (trip_id 나 total 은 건들지 않음)
* 랭그래프가 이 변화된 상태를 받아서 기존 상태에 합친다. 
 * 과연 어떻게 합치는건지?
 
Reducer (누적)
* operator.add (함수값) : 랭그래프가 add함수로 합치는 것
* 덮어쓰지 않고 add 연산으로 합친다.
* reducer 를 붙이지 않으면 기본적으로 덮어쓰게 됨
"""

