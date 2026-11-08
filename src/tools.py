"""

nodes.py 에 보면 아래와 같이 하드코딩

RECEIPTS = {
    "T-2026-03": [
        {"item": "항공권", "amount": 820000},
        {"item": "호텔", "amount": 540000},
        {"item": "식비", "amount": 43000},
    ],
}


* 원래는 함수를 호출 
* tool은 모델이 부르는 것 (모델이 이 이름의 함수를 이런 인자를 기반으로 불러줘)
    * 그걸 받고 실제로 실행하고 나서 그 결과값을 모델에게 준다. 
    * 모델이 함수를 직접 실행하는 게 아님. 모델은 이름과 인자만 만들어내고, 실행은 우리가 작성한 코드가 한 것 (일반함수와 툴과 차이가 없다)
"""

from langchain_core.tools import tool

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

RATES = {"USD": 1350, "JPY": 9, "EUR": 1460}

# LIMITS = {"항공권": 1000000, "호텔": 2000000, "식비": 50000, "택시": 50000}
LIMITS = {"항공권": 1000000, "호텔": 1500000, "식비": 50000, "택시": 50000}



# 모델이 이러한 값을 직접 만들어내지 않고 함수를 통해서 진행된다
# decorator를 붙이면 된다. 
@tool
def list_receipts(trip_id: str) -> list[dict]:
    """출장 번호로 영수증 목록을 가져온다."""
    return RECEIPTS.get(trip_id, [])


@tool
def get_rate(currency: str) -> int:
    """통화 코드의 원화 환율을 가져온다."""
    return RATES.get(currency.upper(), 0)


@tool
def check_policy(item: str, amount: int) -> str:
    """항목과 원화 금액이 사내 규정 한도 안인지 확인한다."""
    limit = LIMITS.get(item)
    if limit is None:
        return f"{item}은 한도가 정해져 있지 않습니다"
    if amount > limit:
        return f"{item} {amount}원은 한도 {limit}원을 넘습니다"
    return f"{item} {amount}원은 한도 {limit}원 안입니다"

ALL_TOOLS = [list_receipts, get_rate, check_policy]




"""
* docker compose exec app python -c "import sys; sys.path.insert(0, 'src'); import json; from tools import check_policy; print('이름:', check_policy.name); print('설명:', check_policy.description); print('스키마:', json.dumps(check_policy.args, ensure_ascii=False))"

-----------[결과]-----------------
이름: check_policy
설명: 항목과 원화 금액이 사내 규정 한도 안인지 확인한다.
스키마: {"item": {"title": "Item", "type": "string"}, "amount": {"title": "Amount", "type": "integer"}}
---------------------------------

- 3b 모델 자체가 그렇게 좋은 성능의 모델은 아니다. 
    - 툴 설명 자체를 직관적이고 명확하게 적어야 한다.
- tool이 들어갔다고 해서 모델 전용이라는 의미는 아니다 (그냥 함수 사용하듯이 사용할 수 있음)


- 모델에게 넘겨서 직접 선택권을 줄 수 있도록 해야 함
'''
docker compose exec app python -c "import os, sys; sys.path.insert(0, 'src'); from langchain_ollama import ChatOllama; from tools import list_receipts, get_rate; model = ChatOllama(model='qwen2.5:3b', base_url=os.environ['OLLAMA_URL'], temperature=0); bound = model.bind_tools([list_receipts, get_rate]); ai = bound.invoke('출장 T-2026-03의 영수증을 가져와 주세요'); print('본문:', repr(ai.content)); print('도구 호출:', ai.tool_calls)"
'''


--------- 결과 --------------
본문: ''
도구 호출: [{'name': 'list_receipts', 'args': {'trip_id': 'T-2026-03'}, 'id': '558fc62d-22b2-40c0-a1d1-c563a3abe6d8', 'type': 'tool_call'}]
-----------------------------
* 본문이 '' : 모델이 문장을 생성하지는 않는다. 
* 대신, 어떤 도구를 부르고자 하는지가 나온다
* name, args : 이름과 인자가 들어가게 된다 (trip_id 에 해당하는 영수증을 반환)

* id -> 도구를 두 번 부를 경우에 대해서 고려한 형태
* 동작한게 아님 (모델은 도구 리스트만 가지고 온 것, 실행은 개발자가 해야 한다.)




'''
docker compose exec app python -c "import os, sys; sys.path.insert(0, 'src'); from langchain_core.messages import HumanMessage, ToolMessage; from langchain_ollama import ChatOllama; from tools import list_receipts, get_rate; model = ChatOllama(model='qwen2.5:3b', base_url=os.environ['OLLAMA_URL'], temperature=0); bound = model.bind_tools([list_receipts, get_rate]); by_name = {'list_receipts': list_receipts, 'get_rate': get_rate}; msgs = [HumanMessage('출장 T-2026-03의 영수증을 가져와 주세요')]; ai = bound.invoke(msgs); msgs.append(ai); exec('for tc in ai.tool_calls:\n    result = by_name[tc[\'name\']].invoke(tc[\'args\'])\n    msgs.append(ToolMessage(content=str(result), tool_call_id=tc[\'id\']))'); print(msgs[-1].content); print(); print('다음 차례:', repr(bound.invoke(msgs).content)[:120])"
'''

- ToolMessage에 append 해서 모델에게 넘긴다. 그 모델이 결과물을 보고 다음을 정한다.


--------- 결과 --------------
다음 차례: '출장 번호 T-2026-03의 영수증 목록이 준비되었습니다.\n\n1. 항공권: 820,000 KRW (환율: 1 USD = 1,475 KRW)\n2. 호텔: 1200 USD (환율: 1 USD = 1,475 KR
----------------------------

- 실행 스크립트를 보면, toolcall_id 로 페어를 맞춘 걸 볼 수 있다.
- 페어를 맞추지 않으면, 모델 입장에서 어떤 요청의 결과인지 알 수 없다.





"""