from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    confirmed: Optional[bool]  # 用户确认状态
    user_input: Optional[str]  # 用户输入的确认信息